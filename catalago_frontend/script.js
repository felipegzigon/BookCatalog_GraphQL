const API_URL = "http://127.0.0.1:8000/graphql";

async function gql(query, variables = {}) {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query,
                variables
            })
        });

        if (!response.ok) {
            throw new Error(
                `Erro HTTP: ${response.status}`
            );
        }

        const result = await response.json();

        if (result.errors) {
            throw new Error(
                result.errors.map(e => e.message).join("\n")
            );
        }

        return result.data;

    } catch (error) {
        throw error;
    }
}

async function loadBooks() {
    const query = `
        query GetBooks(
            $status: ReadingStatus,
            $search: String
        ) {
            books(status: $status, search: $search) {
                id
                title
                year
                pages
                status
                rating
                author {
                    name
                }
            }
        }
    `;

    const variables = {
        status: document.getElementById("statusFilter").value || null,
        search: document.getElementById("search").value || null
    };

    const data = await gql(query, variables);

    renderBooks(data.books);
}

async function loadAuthors() {
    const query = `
        query {
            authors {
                id
                name
            }
        }
    `;

    const data = await gql(query);

    const select = document.getElementById("authorId");

    data.authors.forEach(author => {
        const option = document.createElement("option");

        option.value = author.id;
        option.textContent = author.name;

        select.appendChild(option);
    });
}

document.getElementById("bookForm")
    .addEventListener("submit", async (event) => {

        event.preventDefault();

        const query = `
            mutation AddBook($input: BookInput!) {
                addBook(input: $input) {
                    id
                    title
                }
            }
        `;

        const variables = {
            input: {
                title: document.getElementById("title").value,
                year: Number(document.getElementById("year").value),
                pages: Number(document.getElementById("pages").value),
                authorId: Number(document.getElementById("authorId").value)
            }
        };

        try {
            await gql(query, variables);

            event.target.reset();

            await refreshData();

        } catch (error) {
            showError(error.message);
        }
    });
    
async function refreshData() {
    await Promise.all([
        loadBooks(),
        loadStats()
    ]);
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadAuthors();
        await refreshData();
    } catch (error) {
        showError(error.message);
    }
});

document.getElementById("statusFilter")
    .addEventListener("change", loadBooks);

document.getElementById("search")
    .addEventListener("input", loadBooks);