CREATE DATABASE ChatDB;
GO
USE ChatDB;
GO

CREATE SCHEMA chat;
GO

CREATE TABLE chat.users (
    id              BIGINT          PRIMARY KEY IDENTITY(1,1),
    nickname        VARCHAR(20)     NOT NULL,
    email           VARCHAR(50)     NOT NULL UNIQUE,
    password        VARCHAR(120)    NOT NULL,
    phone_number    VARCHAR(20)     NULL,
    user_role       VARCHAR(20)     NOT NULL DEFAULT 'user',
    creation_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    public_key      VARCHAR(500)    NULL
);
GO

CREATE TABLE chat.access_tokens (
    id              BIGINT          PRIMARY KEY IDENTITY(1,1),
    [user]          BIGINT          NOT NULL,
    token           VARCHAR(500)    NOT NULL,
    token_status    INT             NOT NULL DEFAULT 1,
    creation_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_access_tokens_user FOREIGN KEY ([user]) REFERENCES chat.users(id)
);
GO

CREATE TABLE chat.contacts (
    id              BIGINT          PRIMARY KEY IDENTITY(1,1),
    [user]          BIGINT          NOT NULL,
    contact         BIGINT          NOT NULL,
    creation_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_contacts_user FOREIGN KEY ([user]) REFERENCES chat.users(id),
    CONSTRAINT FK_contacts_contact FOREIGN KEY (contact) REFERENCES chat.users(id)
);
GO

CREATE TABLE chat.rooms (
    id              BIGINT          PRIMARY KEY IDENTITY(1,1),
    room_name       VARCHAR(20)     NOT NULL,
    description     VARCHAR(60)     NULL,
    creation_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date   DATETIME        NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE chat.room_members (
    id                  BIGINT          PRIMARY KEY IDENTITY(1,1),
    room                BIGINT          NOT NULL,
    member              BIGINT          NOT NULL,
    creation_date       DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date       DATETIME        NOT NULL DEFAULT GETDATE(),
    encrypted_room_key  VARCHAR(500)    NULL,
    key_provider        BIGINT          NULL,
    CONSTRAINT FK_room_members_room FOREIGN KEY (room) REFERENCES chat.rooms(id),
    CONSTRAINT FK_room_members_member FOREIGN KEY (member) REFERENCES chat.users(id)
);
GO

CREATE TABLE chat.messages (
    id              BIGINT          PRIMARY KEY IDENTITY(1,1),
    sender          BIGINT          NOT NULL,
    receiver        BIGINT          NOT NULL,
    [content]       VARCHAR(1024)   NOT NULL,
    message_type    VARCHAR(10)     NOT NULL DEFAULT 'text',
    status          INT             NOT NULL DEFAULT 0,
    room            BIGINT          NULL,
    media           VARCHAR(120)    NULL,
    creation_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    modified_date   DATETIME        NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_messages_sender FOREIGN KEY (sender) REFERENCES chat.users(id),
    CONSTRAINT FK_messages_receiver FOREIGN KEY (receiver) REFERENCES chat.users(id),
    CONSTRAINT FK_messages_room FOREIGN KEY (room) REFERENCES chat.rooms(id)
);
GO

CREATE INDEX IX_access_tokens_user ON chat.access_tokens([user]);
CREATE INDEX IX_access_tokens_token ON chat.access_tokens(token);
CREATE INDEX IX_contacts_user ON chat.contacts([user]);
CREATE INDEX IX_contacts_contact ON chat.contacts(contact);
CREATE INDEX IX_room_members_room ON chat.room_members(room);
CREATE INDEX IX_room_members_member ON chat.room_members(member);
CREATE INDEX IX_messages_sender ON chat.messages(sender);
CREATE INDEX IX_messages_receiver ON chat.messages(receiver);
CREATE INDEX IX_messages_room ON chat.messages(room);
GO