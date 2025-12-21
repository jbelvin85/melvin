# Database Schema

## PostgreSQL (Relational)

The relational database is managed with SQLAlchemy and Alembic for migrations.

### `users` table
- `id`: Primary key, integer.
- `username`: Unique username, string.
- `password_hash`: Hashed password, string.
- `is_admin`: Boolean flag for admin users.
- `created_at`: Timestamp of user creation.

### `account_requests` table
- `id`: Primary key, integer.
- `username`: Requested username, string.
- `password_hash`: Hashed password for the requested account.
- `status`: Request status (pending, approved, denied), enum.
- `created_at`: Timestamp of request creation.
- `updated_at`: Timestamp of last status update.

### `conversations` table
- `id`: Primary key, integer.
- `user_id`: Foreign key to `users.id`.
- `title`: Title of the conversation, string.
- `created_at`: Timestamp of conversation creation.

## MongoDB (Document)

The document database is used for storing conversation transcripts.

### `messages` collection
- `_id`: Primary key, ObjectId.
- `conversation_id`: Foreign key to `conversations.id` in the PostgreSQL database.
- `sender`: The sender of the message (e.g., "user" or "melvin").
- `content`: The content of the message.
- `created_at`: Timestamp of message creation.

## Relationships

- A `User` can have multiple `Conversation`s.
- A `Conversation` belongs to one `User`.
- A `Conversation` can have multiple `Message`s (stored in MongoDB).
