/**
 * photon_ac.js — Autocomplete de dirección con Photon (OpenStreetMap), sin API key
 *
 * Uso:
 *   initPhotonAC({
 *     streetInput: 'shippingStreet',   // ID del campo de calle
 *     cityField:   'shippingCity',
 *     postField:   'shippingPostal',
 *     stateField:  'shippingState',
 *     countryField:'shippingCountry',  // select con opciones value="ES"
 *     lang: 'es',                      // idioma para resultados Photon
 *     onSelect: function(feature) {}   // callback opcional tras seleccionar
 *   });
 */
(function () {
  'use strict';

  var PHOTON_URL = 'https://photon.komoot.io/api/';

  function debounce(fn, delay) {
    var t;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, delay);
    };
  }

  function formatLabel(props) {
    var parts = [];
    var street = '';
    if (props.housenumber && props.street) {
      street = props.street + ' ' + props.housenumber;
    } else if (props.street) {
      street = props.street;
    } else if (props.name && props.type !== 'city' && props.type !== 'state' && props.type !== 'country') {
      street = props.name;
    }
    if (street) parts.push(street);
    if (props.city) parts.push(props.city);
    else if (props.locality) parts.push(props.locality);
    if (props.postcode) parts.push(props.postcode);
    if (props.country) parts.push(props.country);
    return parts.join(', ');
  }

  function fillStreet(props) {
    if (props.housenumber && props.street) {
      return props.street + ' ' + props.housenumber;
    } else if (props.street) {
      return props.street;
    } else if (props.name) {
      return props.name;
    }
    return '';
  }

  function initPhotonAC(opts) {
    var streetEl  = document.getElementById(opts.streetInput);
    if (!streetEl) return;

    var cityEl    = document.getElementById(opts.cityField);
    var postEl    = document.getElementById(opts.postField);
    var stateEl   = document.getElementById(opts.stateField);
    var countryEl = document.getElementById(opts.countryField);
    var lang      = opts.lang || 'es';

    /* ── Dropdown container ─────────────────────────────────────── */
    var dropdown = document.createElement('div');
    dropdown.id = 'photon-dropdown-' + opts.streetInput;
    dropdown.style.cssText = [
      'position:absolute',
      'top:100%',
      'left:0',
      'right:0',
      'background:#fff',
      'border:1px solid #d1d5db',
      'border-radius:10px',
      'box-shadow:0 8px 24px rgba(0,0,0,.12)',
      'z-index:9999',
      'display:none',
      'max-height:220px',
      'overflow-y:auto',
      'margin-top:2px'
    ].join(';');

    var wrapper = streetEl.parentElement;
    var origPos = window.getComputedStyle(wrapper).position;
    if (origPos === 'static') wrapper.style.position = 'relative';
    wrapper.appendChild(dropdown);

    /* ── Fetch & render ─────────────────────────────────────────── */
    function closeDropdown() {
      dropdown.style.display = 'none';
    }

    function fetchSuggestions(query) {
      if (!query || query.length < 4) { dropdown.style.display = 'none'; return; }

      var url = PHOTON_URL + '?q=' + encodeURIComponent(query) + '&limit=5&lang=' + lang;

      if (countryEl && countryEl.value) {
        url += '&countrycodes=' + countryEl.value.toLowerCase();
      }

      fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
          dropdown.innerHTML = '';
          var features = (data && data.features) || [];
          if (!features.length) { dropdown.style.display = 'none'; return; }

          features.forEach(function (f) {
            var label = formatLabel(f.properties);
            if (!label) return;
            var item = document.createElement('div');
            item.style.cssText = 'padding:10px 14px;cursor:pointer;font-size:13px;color:#374151;border-bottom:1px solid #f3f4f6;line-height:1.4';
            item.textContent = label;
            item.addEventListener('mouseenter', function () { item.style.background = '#f0fdf4'; });
            item.addEventListener('mouseleave', function () { item.style.background = '#fff'; });
            item.addEventListener('mousedown', function (e) {
              e.preventDefault(); // no blur before click
              applyFeature(f);
            });
            dropdown.appendChild(item);
          });

          dropdown.style.display = 'block';
        })
        .catch(function () { dropdown.style.display = 'none'; });
    }

    function applyFeature(f) {
      var props = f.properties;

      /* Street field */
      var street = fillStreet(props);
      if (street) streetEl.value = street;

      /* City */
      if (cityEl) {
        var city = props.city || props.locality || props.district || '';
        if (city) cityEl.value = city;
      }

      /* Postcode */
      if (postEl && props.postcode) postEl.value = props.postcode;

      /* State / Province */
      if (stateEl && props.state) stateEl.value = props.state;

      /* Country select */
      if (countryEl && props.countrycode) {
        var cc = props.countrycode.toUpperCase();
        var opt = countryEl.querySelector('option[value="' + cc + '"]');
        if (opt) {
          countryEl.value = cc;
          countryEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }

      dropdown.style.display = 'none';

      if (typeof opts.onSelect === 'function') opts.onSelect(f);
    }

    /* ── Listeners ──────────────────────────────────────────────── */
    streetEl.setAttribute('autocomplete', 'off');

    streetEl.addEventListener('input', debounce(function () {
      fetchSuggestions(streetEl.value.trim());
    }, 320));

    streetEl.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') dropdown.style.display = 'none';
    });

    document.addEventListener('click', function (e) {
      if (!wrapper.contains(e.target)) dropdown.style.display = 'none';
    });

    if (countryEl) {
      countryEl.addEventListener('change', function () {
        dropdown.style.display = 'none';
      });
    }

    return { close: closeDropdown };
  }

  window.initPhotonAC = initPhotonAC;
})();
