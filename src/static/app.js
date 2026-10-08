import * as api from "./api.js";
import { resources, localToday } from "./resources.js";
import { renderForm, readFormData } from "./form.js";
import { renderTable } from "./table.js";

// Состояние страницы хранится здесь. Остальные модули получают его аргументами
const data = { authors: [], books: [], readers: [], loans: [] };
let activeResource = "authors";
let editingId = null;

const form = document.querySelector("#item-form");
const submitButton = document.querySelector("#submit-button");
const message = document.querySelector("#message");
const tabs = document.querySelectorAll(".tab");

async function loadData() {
  const names = Object.keys(resources);
  const lists = await Promise.all(names.map(name => api.listItems(name)));

  for (let index = 0; index < names.length; index++) {
    data[names[index]] = lists[index];
  }
  renderPage();
}

function renderPage() {
  renderTable(activeResource, data, {
    edit: editItem,
    delete: deleteItem,
    returnLoan,
  });
  showForm();
}

function showForm() {
  const item = data[activeResource].find(item => item.id === editingId);
  renderForm(activeResource, data, item);
}

function showMessage(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
  message.hidden = false;
}

function clearMessage() {
  message.hidden = true;
}

function selectResource(resource) {
  activeResource = resource;
  editingId = null;
  for (const tab of tabs) {
    tab.classList.toggle("active", tab.dataset.resource === resource);
  }
  clearMessage();
  renderPage();
}

function editItem(id) {
  editingId = id;
  clearMessage();
  showForm();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function cancelEdit() {
  editingId = null;
  clearMessage();
  showForm();
}

async function saveItem(event) {
  event.preventDefault();
  const resource = activeResource;
  const id = editingId;
  const payload = readFormData(form, resource);
  submitButton.disabled = true;

  try {
    let successMessage;
    if (id === null) {
      await api.createItem(resource, payload);
      successMessage = "Запись добавлена";
    } else {
      await api.updateItem(resource, id, payload);
      successMessage = "Изменения сохранены";
    }

    if (activeResource === resource && editingId === id) {
      editingId = null;
    }
    await loadData();
    showMessage(successMessage);
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
}

async function deleteItem(id) {
  if (!confirm("Удалить запись? Это действие нельзя отменить.")) {
    return;
  }
  const resource = activeResource;

  try {
    await api.deleteItem(resource, id);
    if (activeResource === resource && editingId === id) {
      editingId = null;
    }
    await loadData();
    showMessage("Запись удалена");
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function returnLoan(loan) {
  const payload = {
    book_id: loan.book_id,
    reader_id: loan.reader_id,
    issued_on: loan.issued_on,
    due_on: loan.due_on,
    returned_on: localToday(),
  };

  try {
    await api.updateItem("loans", loan.id, payload);
    await loadData();
    showMessage("Возврат отмечен");
  } catch (error) {
    showMessage(error.message, true);
  }
}

// Подключение событий и первая загрузка данных.
form.addEventListener("submit", saveItem);
document.querySelector("#cancel-edit").addEventListener("click", cancelEdit);
for (const tab of tabs) {
  tab.addEventListener("click", () => selectResource(tab.dataset.resource));
}
loadData().catch(error => {
  showMessage(`Не удалось загрузить данные: ${error.message}`, true);
});
