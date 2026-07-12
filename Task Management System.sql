create database Task_Management
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(150) UNIQUE NOT NULL,
    password NVARCHAR(MAX) NOT NULL,

    role NVARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'employee')),

    created_at DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE projects (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(150) NOT NULL,
    description NVARCHAR(MAX),

    created_by INT NULL,
    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_projects_user
    FOREIGN KEY (created_by)
    REFERENCES users(id)
    ON DELETE SET NULL
);
GO


CREATE TABLE tasks (
    id INT IDENTITY(1,1) PRIMARY KEY,

    title NVARCHAR(150) NOT NULL,
    description NVARCHAR(MAX),

    status NVARCHAR(20) NOT NULL DEFAULT 'todo'
        CHECK (status IN ('todo', 'in_progress', 'done')),

    priority NVARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high')),

    user_id INT NULL,
    project_id INT NOT NULL,

    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_tasks_user
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE SET NULL,

    CONSTRAINT FK_tasks_project
    FOREIGN KEY (project_id)
    REFERENCES projects(id)
    ON DELETE CASCADE
);
GO

CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
GO


CREATE TRIGGER trg_update_tasks_updated_at
ON tasks
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE tasks
    SET updated_at = GETDATE()
    FROM tasks t
    INNER JOIN inserted i ON t.id = i.id;
END;
GO


CREATE TABLE comments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    content NVARCHAR(MAX) NOT NULL,

    task_id INT NOT NULL,
    user_id INT NOT NULL,

    created_at DATETIME DEFAULT GETDATE(),

    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
GO




