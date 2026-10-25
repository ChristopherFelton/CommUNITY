// Shared JavaScript for CommUNITY pages. Each helper only runs if its elements are on the page.
// These checks are only for usability; the backend validates everything for real.

// ---------- Character counter ----------
// Any element with data-char-count-for="<field id>" shows "N / max characters" for that field.
document.querySelectorAll("[data-char-count-for]").forEach((counter) => {
  const field = document.getElementById(counter.dataset.charCountFor);
  if (!field) return;

  const max = field.getAttribute("maxlength");
  const update = () => {
    counter.textContent = `${field.value.length} / ${max} characters`;
  };

  field.addEventListener("input", update);
  update();
});

// ---------- Event form: the end time must be after the start time ----------
const eventForm = document.getElementById("event-form");

if (eventForm) {
  const startTime = eventForm.elements.start_time;
  const endTime = eventForm.elements.end_time;
  const timeError = document.getElementById("time-error");

  // Time inputs give "HH:MM" (24-hour), so comparing the strings compares the times.
  const timesAreValid = () => !startTime.value || !endTime.value || endTime.value > startTime.value;

  // Show or hide the inline message, and return whether the times are OK.
  const checkTimes = () => {
    const valid = timesAreValid();
    timeError.hidden = valid;
    endTime.setAttribute("aria-invalid", valid ? "false" : "true");
    return valid;
  };

  startTime.addEventListener("change", checkTimes);
  endTime.addEventListener("change", checkTimes);

  // Block the submit and move focus to the end time if the times don't make sense.
  eventForm.addEventListener("submit", (event) => {
    if (!checkTimes()) {
      event.preventDefault();
      endTime.focus();
    }
  });
}

// ---------- Small DOM helper ----------
// Creates an element with attributes and optional text. Text always goes in with textContent,
// never innerHTML, so anything a person types is shown as plain text.
function createEl(tag, attributes = {}, text = "") {
  const element = document.createElement(tag);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  if (text) element.textContent = text;
  return element;
}

// A small check mark for selected chips (decorative).
function createCheckIcon() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 16 16");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  svg.setAttribute("class", "chip-check-icon");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M3.5 8.5l3 3 6-7");
  svg.appendChild(path);
  return svg;
}

// ---------- Chip picker (skills and interests) ----------
// Turns <div data-chip-picker data-name="skills" data-label="skills" [data-required]> into a
// searchable bubble picker. The server renders plain checkboxes inside it (so the form works
// without JavaScript); this reads them for the suggestions and any saved picks, then replaces them.
// Each selected chip is submitted as its own hidden <input name="..."> so the backend gets a list.
// Optional data-form="<form id>" gives those hidden inputs a form attribute (for pickers outside their form).
const chipPickers = new WeakMap(); // picker element -> { isValid, validate, reset }
const MAX_CHIP_LENGTH = 30;

function initChipPicker(root) {
  const name = root.dataset.name;
  const label = root.dataset.label || name;
  const required = root.hasAttribute("data-required");
  const formId = root.dataset.form;
  const fallback = root.querySelector(".chip-fallback");
  const boxes = Array.from(fallback.querySelectorAll('input[type="checkbox"]'));

  const suggestions = boxes.filter((box) => !box.hasAttribute("data-custom")).map((box) => box.value);
  const selected = boxes.filter((box) => box.checked).map((box) => box.value);
  const initial = selected.slice(); // for reset()
  fallback.remove(); // the checkboxes are replaced by the bubbles below

  const lower = (text) => text.toLowerCase();
  const findIndex = (list, value) => list.findIndex((item) => lower(item) === lower(value));
  const isSelected = (value) => findIndex(selected, value) !== -1;

  // Build the picker: search box, hint, suggestion cloud, "Your picks", hidden inputs, announcer.
  const searchId = `${name}-search`;
  const hintId = `${name}-search-hint`;
  const searchLabel = createEl("label", { for: searchId, class: "visually-hidden" }, `Search or add ${label}`);
  const search = createEl("input", {
    type: "search", id: searchId, class: "chip-search", placeholder: "Search or add your own",
    autocomplete: "off", maxlength: String(MAX_CHIP_LENGTH), "aria-describedby": hintId,
  });
  const hint = createEl("p", { id: hintId, class: "chip-hint" }, "Press Enter to add your own.");
  const cloud = createEl("div", { class: "chip-cloud", role: "group", "aria-label": `Suggested ${label}` });
  const picksTitle = createEl("p", { class: "chip-picks-title" });
  const picks = createEl("ul", { class: "chip-picks" });
  const hiddenInputs = createEl("div", { hidden: "" });
  const announcer = createEl("p", { class: "visually-hidden", "aria-live": "polite" });
  root.append(searchLabel, search, hint, cloud, picksTitle, picks, hiddenInputs, announcer);

  const step = root.closest("[data-step]") || root.parentElement;
  const errorBox = step.querySelector("[data-step-error]");

  // One suggestion bubble per suggested value.
  const bubbles = suggestions.map((value) => {
    const bubble = createEl("button", { type: "button", class: "chip", "aria-pressed": "false" });
    bubble.append(createCheckIcon(), createEl("span", { class: "chip-text" }, value));
    bubble.addEventListener("click", () => toggle(value));
    cloud.appendChild(bubble);
    return { value, bubble };
  });

  const announce = (message) => {
    const count = selected.length;
    announcer.textContent = `${message} ${count} ${count === 1 ? label.replace(/s$/, "") : label} picked.`;
  };

  // Redraw everything from `selected` and the current search text.
  function render() {
    const query = lower(search.value.trim());

    let matches = 0;
    bubbles.forEach(({ value, bubble }) => {
      bubble.setAttribute("aria-pressed", isSelected(value) ? "true" : "false");
      const visible = !query || lower(value).includes(query);
      bubble.hidden = !visible;
      if (visible) matches += 1;
    });

    const typed = search.value.trim().slice(0, MAX_CHIP_LENGTH);
    if (typed && matches === 0 && !isSelected(typed)) {
      hint.textContent = `Press Enter to add "${typed}"`;
    } else {
      hint.textContent = "Press Enter to add your own.";
    }

    picksTitle.textContent = `Your picks (${selected.length})`;
    picks.replaceChildren(...selected.map((value) => {
      const item = createEl("li", { class: "chip chip--picked" });
      const remove = createEl("button", { type: "button", class: "chip-remove", "aria-label": `Remove ${value}` });
      remove.appendChild(createEl("span", { "aria-hidden": "true" }, "×"));
      remove.addEventListener("click", () => {
        removeValue(value);
        search.focus(); // the button is gone, so keep focus somewhere sensible
      });
      item.append(createEl("span", { class: "chip-text" }, value), remove);
      return item;
    }));

    hiddenInputs.replaceChildren(...selected.map((value) => createEl("input", formId ? { type: "hidden", name, value, form: formId } : { type: "hidden", name, value })));
  }

  function addValue(raw) {
    const value = raw.trim().slice(0, MAX_CHIP_LENGTH);
    if (!value) return;
    if (isSelected(value)) {
      announce(`${selected[findIndex(selected, value)]} is already picked.`);
      return;
    }
    // Typing a suggestion's name picks that suggestion (keeping its spelling).
    const suggestion = suggestions[findIndex(suggestions, value)];
    selected.push(suggestion || value);
    clearError();
    render();
    announce(`${suggestion || value} added.`);
  }

  function removeValue(value) {
    const index = findIndex(selected, value);
    if (index === -1) return;
    const [removed] = selected.splice(index, 1);
    render();
    announce(`${removed} removed.`);
  }

  function toggle(value) {
    if (isSelected(value)) removeValue(value);
    else addValue(value);
  }

  function clearError() {
    if (errorBox) errorBox.hidden = true;
    search.removeAttribute("aria-invalid");
  }

  search.addEventListener("input", render);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      // Enter adds a chip here; it must not move to the next step or submit the form.
      event.preventDefault();
      event.stopPropagation();
      addValue(search.value);
      search.value = "";
      render();
    } else if (event.key === "Escape" && search.value) {
      event.preventDefault();
      search.value = "";
      render();
    }
  });

  render();

  // Used by the step flow: "at least one" pickers need a pick before moving on.
  chipPickers.set(root, {
    isValid: () => !required || selected.length > 0,
    validate() {
      if (!required || selected.length > 0) {
        clearError();
        return true;
      }
      if (errorBox) {
        errorBox.textContent = `Please pick at least one of your ${label}.`;
        errorBox.hidden = false;
      }
      search.setAttribute("aria-invalid", "true");
      search.focus();
      return false;
    },
    // Puts the picks back the way the page loaded them (e.g. a "Cancel" button).
    reset() {
      selected.splice(0, selected.length, ...initial);
      search.value = "";
      clearError();
      render();
    },
  });
}

document.querySelectorAll("[data-chip-picker]").forEach(initChipPicker);

// ---------- Onboarding: one question at a time ----------
// Without JavaScript every question shows on one page. With it, only the current step shows,
// with a progress bar and Back / Next buttons. Nothing is saved in the browser.
const onboardingForm = document.getElementById("onboarding-form");

if (onboardingForm) {
  const steps = Array.from(onboardingForm.querySelectorAll("[data-step]"));
  const progress = document.querySelector("[data-progress]");
  const progressBar = progress.querySelector('[role="progressbar"]');
  const progressFill = progress.querySelector("[data-progress-fill]");
  const stepNumber = progress.querySelector("[data-step-number]");
  const backButton = onboardingForm.querySelector("[data-step-back]");
  const nextButton = onboardingForm.querySelector("[data-step-next]");
  const submitButton = onboardingForm.querySelector("[data-step-submit]");
  let current = 0;

  progress.querySelector("[data-step-total]").textContent = steps.length;
  progressBar.setAttribute("aria-valuemax", steps.length);
  onboardingForm.classList.add("is-stepped");
  progress.hidden = false;

  // "A specific date": the date field only shows (and is required) when that option is picked.
  const deadlineField = onboardingForm.querySelector("[data-deadline]");
  const deadline = deadlineField.querySelector("input");
  const today = new Date();
  deadline.min = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, "0"), String(today.getDate()).padStart(2, "0")].join("-");

  function updateDeadline() {
    const custom = onboardingForm.elements.time_period.value === "custom";
    deadlineField.hidden = !custom;
    deadline.disabled = !custom;
    deadline.required = custom;
  }
  onboardingForm.querySelectorAll('input[name="time_period"]').forEach((radio) => radio.addEventListener("change", updateDeadline));
  updateDeadline();

  function showStep(index, moveFocus) {
    onboardingForm.dataset.direction = index < current ? "back" : "forward";
    current = index;
    steps.forEach((step, i) => step.classList.toggle("is-active", i === index));

    stepNumber.textContent = index + 1;
    progressBar.setAttribute("aria-valuenow", index + 1);
    progressFill.style.width = `${((index + 1) / steps.length) * 100}%`;

    const last = index === steps.length - 1;
    backButton.hidden = index === 0;
    nextButton.hidden = last;
    submitButton.hidden = !last;

    // Move focus to the new question so keyboard and screen reader users land on it.
    if (moveFocus) steps[index].querySelector(".step-question").focus();
  }

  // Check only the fields in one step, using the browser's own validation rules.
  function validateStep(step) {
    const errorBox = step.querySelector("[data-step-error]");
    errorBox.hidden = true;
    step.querySelectorAll("[aria-invalid]").forEach((field) => field.removeAttribute("aria-invalid"));

    for (const picker of step.querySelectorAll("[data-chip-picker]")) {
      if (!chipPickers.get(picker).validate()) return false;
    }

    const fields = Array.from(step.querySelectorAll("input[name], select[name], textarea[name]"))
      .filter((field) => !field.disabled && field.type !== "hidden");
    const invalid = fields.find((field) => !field.checkValidity());
    if (!invalid) return true;

    errorBox.textContent = invalid.dataset.errorMessage || invalid.validationMessage;
    errorBox.hidden = false;
    invalid.setAttribute("aria-invalid", "true");
    invalid.reportValidity(); // also focuses the field and shows the browser's hint
    return false;
  }

  nextButton.addEventListener("click", () => {
    if (validateStep(steps[current])) showStep(current + 1, true);
  });

  backButton.addEventListener("click", () => showStep(current - 1, true));

  // Enter in a field means "Next" until the last step, where it submits (after the same check).
  onboardingForm.addEventListener("keydown", (event) => {
    const field = event.target;
    if (event.key !== "Enter" || field.tagName !== "INPUT" || field.type === "search") return;
    if (current < steps.length - 1) {
      event.preventDefault();
      nextButton.click();
    } else {
      checkBeforeSubmit(event);
    }
  });

  // Hide an error as soon as the person changes that step's answer.
  onboardingForm.addEventListener("input", (event) => {
    const step = event.target.closest("[data-step]");
    if (step && event.target.type !== "search") step.querySelector("[data-step-error]").hidden = true;
  });

  // A quiet version of validateStep: no messages, just "is this step OK?".
  function stepIsValid(step) {
    const pickersOk = Array.from(step.querySelectorAll("[data-chip-picker]")).every((picker) => chipPickers.get(picker).isValid());
    const fieldsOk = Array.from(step.querySelectorAll("input[name], select[name], textarea[name]"))
      .filter((field) => !field.disabled && field.type !== "hidden")
      .every((field) => field.checkValidity());
    return pickersOk && fieldsOk;
  }

  // Before submitting, re-check every step; jump to the first one that needs attention and show
  // its inline message. This runs on the button click (before the browser's own check, which
  // would only show a popup) and again on submit, just in case.
  function checkBeforeSubmit(event) {
    const firstInvalid = steps.findIndex((step) => !stepIsValid(step));
    if (firstInvalid === -1) return;
    event.preventDefault();
    if (firstInvalid !== current) showStep(firstInvalid, false);
    validateStep(steps[firstInvalid]);
  }

  submitButton.addEventListener("click", checkBeforeSubmit);
  onboardingForm.addEventListener("submit", checkBeforeSubmit);

  showStep(0, false);
}

// ---------- Opportunities: search, sort, and answer bubbles ----------
// Everything here works without JavaScript too (a plain GET form and native <details>);
// this only adds conveniences. Answers live in the form fields only, never in browser storage.
const searchForm = document.getElementById("search-form");

if (searchForm) {
  searchForm.classList.add("has-js");

  // The "x" in the search bar shows while there's text and clears it.
  const query = searchForm.elements.q;
  const clearButton = searchForm.querySelector("[data-search-clear]");
  const syncClear = () => {
    clearButton.hidden = !query.value;
  };
  query.addEventListener("input", syncClear);
  clearButton.addEventListener("click", () => {
    query.value = "";
    syncClear();
    query.focus();
  });
  syncClear();

  // Changing the sort refreshes the results right away (the <noscript> Apply button does this without JS).
  searchForm.querySelectorAll("[data-auto-submit]").forEach((select) => {
    select.addEventListener("change", () => searchForm.requestSubmit());
  });

  // "A specific date": the date field only shows (and is sent) when that option is picked.
  const deadlineField = searchForm.querySelector("[data-deadline]");
  const updateDeadline = () => {
    if (!deadlineField) return;
    const picked = searchForm.querySelector('input[name="time_period"]:checked');
    const custom = Boolean(picked) && picked.value === "custom";
    deadlineField.hidden = !custom;
    deadlineField.querySelector("input").disabled = !custom;
  };
  searchForm.querySelectorAll('input[name="time_period"]').forEach((radio) => radio.addEventListener("change", updateDeadline));
  updateDeadline();

  // One answer panel open at a time. The panel lines up under its bubble without going off-screen,
  // and its first field gets focus.
  const pops = Array.from(searchForm.querySelectorAll("details.answer-pop"));

  const placePanel = (pop) => {
    const panel = pop.querySelector(".answer-panel");
    const row = panel.offsetParent;
    if (!row) return;
    const left = pop.querySelector("summary").offsetLeft;
    panel.style.left = `${Math.max(0, Math.min(left, row.clientWidth - panel.offsetWidth))}px`;
  };

  const firstField = (panel) => {
    const field = panel.querySelector("input:not([type='hidden']):not([disabled]), select");
    if (field && field.type === "radio") {
      return panel.querySelector(`input[name="${field.name}"]:checked`) || field;
    }
    return field;
  };

  const closePop = (pop, returnFocus) => {
    pop.open = false;
    if (returnFocus) pop.querySelector("summary").focus();
  };

  // Puts a panel's fields back to the values the page loaded with.
  const resetPanel = (panel) => {
    panel.querySelectorAll("input:not([type='hidden']), select").forEach((field) => {
      if (field.type === "checkbox" || field.type === "radio") field.checked = field.defaultChecked;
      else if (field.tagName === "SELECT") Array.from(field.options).forEach((option) => { option.selected = option.defaultSelected; });
      else field.value = field.defaultValue;
    });
    panel.querySelectorAll("[data-chip-picker]").forEach((picker) => {
      const api = chipPickers.get(picker);
      if (api) api.reset();
    });
    updateDeadline();
  };

  pops.forEach((pop) => {
    const panel = pop.querySelector(".answer-panel");

    pop.addEventListener("toggle", () => {
      if (!pop.open) return;
      pops.forEach((other) => {
        if (other !== pop) other.open = false;
      });
      placePanel(pop);
      const field = firstField(panel);
      if (field) field.focus();
    });

    const cancel = pop.querySelector("[data-pop-cancel]");
    cancel.hidden = false;
    cancel.addEventListener("click", () => {
      resetPanel(panel);
      closePop(pop, true);
    });
  });

  // A click anywhere outside the open panel closes it. composedPath() is used because some clicks
  // (like removing a chip) take the clicked button out of the page before this runs.
  document.addEventListener("click", (event) => {
    const path = event.composedPath();
    pops.forEach((pop) => {
      if (pop.open && !path.includes(pop)) closePop(pop, false);
    });
  });

  // Escape closes the open panel and puts focus back on its bubble.
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || event.defaultPrevented) return;
    const open = pops.find((pop) => pop.open);
    if (open) {
      event.preventDefault();
      closePop(open, true);
    }
  });

  window.addEventListener("resize", () => {
    const open = pops.find((pop) => pop.open);
    if (open) placePanel(open);
  });

  // If the browser finds an invalid answer (e.g. a 4-digit ZIP) inside a closed bubble,
  // open that bubble so its message can show.
  searchForm.addEventListener("invalid", (event) => {
    const pop = event.target.closest("details.answer-pop");
    if (pop) pop.open = true;
  }, true);
}
