(function () {
  const countrySelect = document.querySelector("[data-country-select]");
  const stateSelect = document.querySelector("[data-state-select]");
  if (!countrySelect || !stateSelect) {
    return;
  }

  const statesUrl = countrySelect.dataset.statesUrl || "/accounts/states/";
  const selectedState = stateSelect.value;

  function setOptions(states, keepValue) {
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = states.length ? "Select state" : "State not available";
    stateSelect.replaceChildren(placeholder);
    states.forEach(function (state) {
      const option = document.createElement("option");
      option.value = state.id;
      option.textContent = state.name;
      if (keepValue && String(state.id) === String(keepValue)) {
        option.selected = true;
      }
      stateSelect.appendChild(option);
    });
    stateSelect.disabled = states.length === 0;
  }

  async function loadStates(keepValue) {
    const countryId = countrySelect.value;
    if (!countryId) {
      setOptions([], "");
      return;
    }
    const response = await fetch(`${statesUrl}?country=${encodeURIComponent(countryId)}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (!response.ok) {
      setOptions([], "");
      return;
    }
    const data = await response.json();
    setOptions(data.states || [], keepValue);
  }

  countrySelect.addEventListener("change", function () {
    loadStates("");
  });

  loadStates(selectedState);
})();
