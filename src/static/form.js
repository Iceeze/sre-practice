import { resources } from "./resources.js";

// Построение формы и преобразование введённых значений в данные для API
export function renderForm(resource, data, item = null) {
  const settings = resources[resource];
  const fields = document.querySelector("#fields");

  document.querySelector("#form-title").textContent = item ? "Редактирование" : settings.createTitle;
  document.querySelector("#submit-button").textContent = item ? "Сохранить" : "Добавить";
  document.querySelector("#cancel-edit").hidden = !item;
  fields.replaceChildren();

  for (const field of settings.fields) {
    fields.append(createField(field, data, item));
  }
}

function createField(field, data, item) {
  const label = document.createElement("label");
  label.className = "field";

  const caption = document.createElement("span");
  caption.textContent = field.label;
  label.append(caption);

  const input = createInput(field, data);
  if (item) {
    input.value = item[field.name] ?? "";
  } else if (field.defaultValue) {
    input.value = field.defaultValue();
  }
  label.append(input);

  if (field.hint) {
    const hint = document.createElement("small");
    hint.textContent = field.hint;
    label.append(hint);
  }
  return label;
}

function createInput(field, data) {
  let input;
  if (field.type === "select") {
    input = createSelect(field.resource, data[field.resource]);
  } else {
    input = document.createElement("input");
    input.type = field.type ?? "text";
  }

  input.name = field.name;
  input.required = Boolean(field.required);
  if (field.min !== undefined) input.min = field.min;
  if (field.max !== undefined) input.max = field.max;
  if (field.placeholder) input.placeholder = field.placeholder;
  return input;
}

function createSelect(resource, items) {
  const select = document.createElement("select");
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Выберите...";
  select.append(placeholder);

  for (const item of items) {
    const option = document.createElement("option");
    option.value = String(item.id);
    option.textContent = resources[resource].optionLabel(item);
    select.append(option);
  }
  return select;
}

export function readFormData(form, resource) {
  const formData = new FormData(form);
  const payload = {};

  for (const field of resources[resource].fields) {
    const value = formData.get(field.name);

    if (value === "" && !field.required) {
      payload[field.name] = null;
    } else if (value !== "" && (field.type === "number" || field.type === "select")) {
      payload[field.name] = Number(value);
    } else {
      payload[field.name] = value;
    }
  }
  return payload;
}
