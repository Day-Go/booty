# Mock Project API Documentation

## Overview

The Mock Project API provides access to users and posts data.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Currently, the API does not require authentication.

## Endpoints

### Users

#### Get all users

```
GET /users
```

Response:
```json
[
  {
    "id": 1,
    "username": "user1",
    "email": "user1@example.com",
    "created_at": "2023-01-01T00:00:00",
    "is_active": true,
    "last_login": null
  },
  {
    "id": 2,
    "username": "user2",
    "email": "user2@example.com",
    "created_at": "2023-01-02T00:00:00",
    "is_active": true,
    "last_login": "2023-01-03T00:00:00"
  }
]
```

#### Get user by ID

```
GET /users/{user_id}
```

Response:
```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com",
  "created_at": "2023-01-01T00:00:00",
  "is_active": true,
  "last_login": null
}
```

### Posts

#### Get all posts

```
GET /posts
```

Response:
```json
[
  {
    "id": 1,
    "title": "First Post",
    "content": "This is the first post content",
    "author_id": 1,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": null,
    "tags": ["test", "example"]
  },
  {
    "id": 2,
    "title": "Second Post",
    "content": "This is the second post content",
    "author_id": 2,
    "created_at": "2023-01-02T00:00:00",
    "updated_at": "2023-01-03T00:00:00",
    "tags": ["example"]
  }
]
```

#### Get post by ID

```
GET /posts/{post_id}
```

Response:
```json
{
  "id": 1,
  "title": "First Post",
  "content": "This is the first post content",
  "author_id": 1,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": null,
  "tags": ["test", "example"]
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- 200: Success
- 404: Resource not found
- 500: Server error

Error response format:
```json
{
  "error": "Error message here"
}
```