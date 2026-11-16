from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
import strawberry
from enum import Enum

@strawberry.enum
class ReadingStatus(Enum):
    WANT_TO_READ = "WANT_TO_READ"
    READING = "READING"
    FINISHED = "FINISHED"

authors = [
    {"id": 1, "name": "J. R. R. Tolkien", "country": "Reino Unido"},
    {"id": 2, "name": "George Orwell", "country": "Reino Unido"},
    {"id": 3, "name": "Machado de Assis", "country": "Brasil"}
]

books = [
    {
        "id": 1,
        "title": "O Hobbit",
        "year": 1937,
        "pages": 310,
        "status": ReadingStatus.FINISHED,
        "rating": 5,
        "authorId": 1
    },
    {
        "id": 2,
        "title": "O Senhor dos Anéis",
        "year": 1954,
        "pages": 1178,
        "status": ReadingStatus.READING,
        "rating": None,
        "authorId": 1
    },
    {
        "id": 3,
        "title": "1984",
        "year": 1949,
        "pages": 328,
        "status": ReadingStatus.FINISHED,
        "rating": 5,
        "authorId": 2
    },
    {
        "id": 4,
        "title": "A Revolução dos Bichos",
        "year": 1945,
        "pages": 152,
        "status": ReadingStatus.WANT_TO_READ,
        "rating": None,
        "authorId": 2
    },
    {
        "id": 5,
        "title": "Dom Casmurro",
        "year": 1899,
        "pages": 256,
        "status": ReadingStatus.FINISHED,
        "rating": 4,
        "authorId": 3
    },
    {
        "id": 6,
        "title": "Memórias Póstumas de Brás Cubas",
        "year": 1881,
        "pages": 368,
        "status": ReadingStatus.READING,
        "rating": None,
        "authorId": 3
    }
]

def find_book(book_id):
    return next(
        (book for book in books if book["id"] == book_id),
        None
    )

def find_author(author_id):
    return next(
        (author for author in authors if author["id"] == author_id),
        None
    )


###
@strawberry.type
class Author:
    id: int
    name: str
    country: str | None

    @strawberry.field
    def books(self) -> list["Book"]:
        return [
            Book(**book)
            for book in books
            if book["authorId"] == self.id
        ]

    @strawberry.field
    def book_count(self) -> int:
        return len([
            book for book in books
            if book["authorId"] == self.id
        ])

@strawberry.type
class Book:
    id: int
    title: str
    year: int
    pages: int
    status: ReadingStatus
    rating: int | None
    authorId: int

    @strawberry.field
    def author(self) -> Author:
        author = find_author(self.authorId)

        if author is None:
            raise ValueError("Autor não encontrado")

        return Author(**author)

@strawberry.type
class Stats:
    total_books: int
    finished_books: int
    average_rating: float | None
    total_pages_read: int

@strawberry.type
class Query:

    @strawberry.field
    def books(
        self,
        status: ReadingStatus | None = None,
        search: str | None = None
    ) -> list[Book]:

        result = books.copy()

        if status is not None:
            result = [
                book for book in result
                if book["status"] == status
            ]

        if search:
            result = [
                book for book in result
                if search.lower() in book["title"].lower()
            ]

        return [Book(**book) for book in result]

    @strawberry.field
    def book(self, id: int) -> Book | None:
        book = find_book(id)
        return Book(**book) if book else None

    @strawberry.field
    def authors(self) -> list[Author]:
        return [Author(**author) for author in authors]

    @strawberry.field
    def stats(self) -> Stats:

        finished = [
            book for book in books
            if book["status"] == ReadingStatus.FINISHED
        ]

        ratings = [
            book["rating"] for book in books
            if book["rating"] is not None
        ]

        average = (
            sum(ratings) / len(ratings)
            if ratings else None
        )

        return Stats(
            total_books=len(books),
            finished_books=len(finished),
            average_rating=average,
            total_pages_read=sum(
                book["pages"] for book in finished
            )
        )

@strawberry.input
class AuthorInput:
    name: str
    country: str | None = None


@strawberry.input
class BookInput:
    title: str
    year: int
    pages: int
    author_id: int

from datetime import date

@strawberry.type
class Mutation:

    @strawberry.mutation
    def add_author(self, input: AuthorInput) -> Author:

        if not input.name.strip():
            raise ValueError("O nome do autor não pode ser vazio")

        new_author = {
            "id": max((a["id"] for a in authors), default=0) + 1,
            "name": input.name.strip(),
            "country": input.country
        }

        authors.append(new_author)

        return Author(**new_author)

    @strawberry.mutation
    def add_book(self, input: BookInput) -> Book:

        if not input.title.strip():
            raise ValueError("O título não pode ser vazio")

        if input.year > date.today().year:
            raise ValueError("O ano não pode ser futuro")

        if input.pages < 1:
            raise ValueError("O número de páginas deve ser maior que zero")

        if not find_author(input.author_id):
            raise ValueError("Autor não encontrado")

        new_book = {
            "id": max((b["id"] for b in books), default=0) + 1,
            "title": input.title.strip(),
            "year": input.year,
            "pages": input.pages,
            "status": ReadingStatus.WANT_TO_READ,
            "rating": None,
            "authorId": input.author_id
        }

        books.append(new_book)

        return Book(**new_book)

    @strawberry.mutation
    def update_book_status(
        self,
        id: int,
        status: ReadingStatus
    ) -> Book:

        book = find_book(id)

        if not book:
            raise ValueError("Livro não encontrado")

        book["status"] = status

        return Book(**book)

    @strawberry.mutation
    def rate_book(self, id: int, rating: int) -> Book:

        book = find_book(id)

        if not book:
            raise ValueError("Livro não encontrado")

        if rating < 1 or rating > 5:
            raise ValueError("A nota deve estar entre 1 e 5")

        if book["status"] != ReadingStatus.FINISHED:
            raise ValueError("Só é possível avaliar livros finalizados")

        book["rating"] = rating

        return Book(**book)

    @strawberry.mutation
    def delete_book(self, id: int) -> bool:

        book = find_book(id)

        if not book:
            raise ValueError("Livro não encontrado")

        books.remove(book)

        return True

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)

graphql_app = GraphQLRouter(schema)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)   

app.include_router(graphql_app, prefix="/graphql")