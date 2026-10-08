async function request(path, method = "GET", data = null) {
  const options = { method };

  if (data !== null) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`/api/${path}`, options);

  if (!response.ok) {
    let message = "Не удалось выполнить запрос";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else {
        message = "Проверьте заполнение полей";
      }
    } catch {
      // Если сервер ответил не JSON, оставляем общее сообщение.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export function listItems(resource) {
  return request(resource);
}

export function createItem(resource, data) {
  return request(resource, "POST", data);
}

export function updateItem(resource, id, data) {
  return request(`${resource}/${id}`, "PUT", data);
}

export function deleteItem(resource, id) {
  return request(`${resource}/${id}`, "DELETE");
}
