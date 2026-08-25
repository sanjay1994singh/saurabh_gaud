(function () {
  const countrySelect = document.querySelector("[data-country-select]");
  const stateSelect = document.querySelector("[data-state-select]");
  if (!countrySelect || !stateSelect) {
    return;
  }

  function enhanceSearchableSelect(select) {
    if (!select.matches("[data-searchable-select]") || select.dataset.enhancedSearch === "true") {
      return;
    }

    select.dataset.enhancedSearch = "true";
    const wrapper = document.createElement("div");
    wrapper.className = "searchable-select";

    const search = document.createElement("input");
    search.type = "search";
    search.className = "searchable-select-input";
    search.autocomplete = "off";
    search.placeholder = select.dataset.searchPlaceholder || "Search";

    const list = document.createElement("div");
    list.className = "searchable-select-list";
    list.hidden = true;

    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(search);
    wrapper.appendChild(list);
    wrapper.appendChild(select);

    function optionRows() {
      return Array.from(select.options).filter(function (option) {
        return option.value;
      });
    }

    function selectedOption() {
      return select.options[select.selectedIndex];
    }

    function syncSearchText() {
      const option = selectedOption();
      search.value = option && option.value ? option.textContent.trim() : "";
    }

    function chooseOption(option) {
      select.value = option.value;
      syncSearchText();
      list.hidden = true;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function renderList() {
      const query = search.value.trim().toLowerCase();
      const matches = optionRows().filter(function (option) {
        return option.textContent.toLowerCase().includes(query);
      });

      list.replaceChildren();
      if (!matches.length) {
        const empty = document.createElement("div");
        empty.className = "searchable-select-empty";
        empty.textContent = select.dataset.emptyText || "No results";
        list.appendChild(empty);
        list.hidden = false;
        return;
      }

      matches.slice(0, 80).forEach(function (option) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "searchable-select-option";
        button.textContent = option.textContent;
        if (option.selected) {
          button.classList.add("is-selected");
        }
        button.addEventListener("mousedown", function (event) {
          event.preventDefault();
          chooseOption(option);
        });
        list.appendChild(button);
      });
      list.hidden = false;
    }

    search.addEventListener("input", renderList);
    search.addEventListener("focus", renderList);
    search.addEventListener("keydown", function (event) {
      const firstOption = list.querySelector(".searchable-select-option");
      if (event.key === "Enter" && firstOption) {
        event.preventDefault();
        firstOption.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
      }
      if (event.key === "Escape") {
        list.hidden = true;
        syncSearchText();
      }
    });
    search.addEventListener("blur", function () {
      window.setTimeout(function () {
        list.hidden = true;
        syncSearchText();
      }, 120);
    });
    select.addEventListener("change", syncSearchText);
    syncSearchText();
  }

  enhanceSearchableSelect(countrySelect);

  const statesUrl = countrySelect.dataset.statesUrl || "/accounts/states/";
  const selectedState = stateSelect.value;

  function setOptions(states, keepValue) {
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = states.length ? "राज्य चुनें" : "राज्य उपलब्ध नहीं है";
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
