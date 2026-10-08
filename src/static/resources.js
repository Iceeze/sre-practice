export function localToday() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function fullName(person) {
  return `${person.first_name} ${person.last_name}`;
}

function personName(people, id) {
  const person = people.find(person => person.id === id);
  if (!person) {
    return `#${id}`;
  }
  return fullName(person);
}

function bookTitle(books, id) {
  const book = books.find(book => book.id === id);
  if (!book) {
    return `#${id}`;
  }
  return book.title;
}

function loanStatus(loan) {
  if (loan.returned_on) {
    return { label: "Возвращена", className: "returned" };
  }
  if (loan.due_on < localToday()) {
    return { label: "Просрочена", className: "overdue" };
  }
  return { label: "На руках", className: "" };
}

export const resources = {
  authors: {
    title: "Авторы",
    createTitle: "Новый автор",
    optionLabel: fullName,
    fields: [
      { name: "first_name", label: "Имя", required: true },
      { name: "last_name", label: "Фамилия", required: true },
    ],
    columns: [
      { label: "Имя", value: fullName },
      {
        label: "Книг",
        value: (author, data) => data.books.filter(book => book.author_id === author.id).length,
      },
    ],
  },
  books: {
    title: "Книги",
    createTitle: "Новая книга",
    optionLabel: book => `${book.title} — ${book.inventory_number}`,
    fields: [
      { name: "title", label: "Название", required: true },
      { name: "isbn", label: "ISBN", required: true },
      { name: "publication_year", label: "Год издания", type: "number", min: 1, max: 9999 },
      { name: "inventory_number", label: "Инвентарный номер", required: true },
      { name: "author_id", label: "Автор", type: "select", resource: "authors", required: true },
    ],
    columns: [
      { label: "Книга", value: book => book.title },
      { label: "Автор", value: (book, data) => personName(data.authors, book.author_id) },
      { label: "ISBN", value: book => book.isbn },
      { label: "Инв. №", value: book => book.inventory_number },
    ],
  },
  readers: {
    title: "Читатели",
    createTitle: "Новый читатель",
    optionLabel: fullName,
    fields: [
      { name: "first_name", label: "Имя", required: true },
      { name: "last_name", label: "Фамилия", required: true },
      {
        name: "phone",
        label: "Телефон",
        type: "tel",
        required: true,
        placeholder: "+79991234567",
        hint: "Международный формат: + и от 8 до 15 цифр",
      },
    ],
    columns: [
      { label: "Читатель", value: fullName },
      { label: "Телефон", value: reader => reader.phone },
    ],
  },
  loans: {
    title: "Выдачи",
    createTitle: "Новая выдача",
    fields: [
      { name: "book_id", label: "Книга", type: "select", resource: "books", required: true },
      { name: "reader_id", label: "Читатель", type: "select", resource: "readers", required: true },
      {
        name: "issued_on",
        label: "Дата выдачи",
        type: "date",
        required: true,
        defaultValue: localToday,
      },
      { name: "due_on", label: "Вернуть до", type: "date", required: true },
      {
        name: "returned_on",
        label: "Дата возврата",
        type: "date",
        hint: "Оставьте пустым, пока книга у читателя",
      },
    ],
    columns: [
      { label: "Книга", value: (loan, data) => bookTitle(data.books, loan.book_id) },
      { label: "Читатель", value: (loan, data) => personName(data.readers, loan.reader_id) },
      { label: "Выдана", value: loan => loan.issued_on },
      { label: "Вернуть до", value: loan => loan.due_on },
      { label: "Состояние", value: loanStatus, badge: true },
    ],
  },
};
