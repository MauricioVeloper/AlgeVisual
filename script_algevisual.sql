-- 1. Crear la base de datos
CREATE DATABASE AlgeVisual;
GO

USE AlgeVisual;
GO

-- 2. Tabla Base: Usuarios (Centraliza la autenticación y roles)
CREATE TABLE Usuarios (
    ID_Usuario INT IDENTITY(1,1) PRIMARY KEY,
    Matricula VARCHAR(50) UNIQUE NULL, -- Puede ser NULL porque un Administrador podría no requerirla
    NombreCompleto VARCHAR(150) NOT NULL,
    Correo VARCHAR(100) UNIQUE NOT NULL,
    Contrasena VARCHAR(255) NOT NULL,
    FotoPerfil VARCHAR(255),
    Rol VARCHAR(20) NOT NULL CHECK (Rol IN ('Estudiante', 'Docente', 'Administrador')),
    Estado BIT DEFAULT 1 -- Baja lógica general
);

-- 3. Tabla Hija: Docentes (Relación 1 a 1 con Usuarios)
CREATE TABLE Docentes (
    ID_Docente INT PRIMARY KEY FOREIGN KEY REFERENCES Usuarios(ID_Usuario),
    Descripcion VARCHAR(200) -- Atributo exclusivo del docente
);

-- 4. Tabla Hija: Estudiantes (Relación 1 a 1 con Usuarios)
CREATE TABLE Estudiantes (
    ID_Estudiante INT PRIMARY KEY FOREIGN KEY REFERENCES Usuarios(ID_Usuario)
    -- Aquí se pueden agregar campos exclusivos de estudiantes en el futuro si se requiere
);

-- 5. Tabla Grupos (Se relaciona con el ID del Docente)
CREATE TABLE Grupos (
    ID_Grupo INT IDENTITY(1,1) PRIMARY KEY,
    CodigoInvitacion VARCHAR(20) UNIQUE NOT NULL,
    Nombre VARCHAR(100) NOT NULL,
    Ciclo VARCHAR(50),
    Horario VARCHAR(100),
    EspacioFisico VARCHAR(100),
    ID_Docente INT NOT NULL FOREIGN KEY REFERENCES Docentes(ID_Docente),
    Estado BIT DEFAULT 1
);

-- 6. Tabla Intermedia: Grupo_Estudiantes (Muchos a Muchos)
CREATE TABLE Grupo_Estudiantes (
    ID_Grupo INT FOREIGN KEY REFERENCES Grupos(ID_Grupo),
    ID_Estudiante INT FOREIGN KEY REFERENCES Estudiantes(ID_Estudiante),
    FechaUnion DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (ID_Grupo, ID_Estudiante)
);

-- 7. Tabla Tareas
CREATE TABLE Tareas (
    ID_Tarea INT IDENTITY(1,1) PRIMARY KEY,
    ID_Grupo INT NOT NULL FOREIGN KEY REFERENCES Grupos(ID_Grupo),
    Titulo VARCHAR(150) NOT NULL,
    Descripcion TEXT,
    ArchivosAdicionales VARCHAR(255),
    FechaAsignacion DATETIME DEFAULT GETDATE(),
    FechaLimite DATETIME NOT NULL,
    Estado BIT DEFAULT 1
);

-- 8. Tabla Entregas
CREATE TABLE Entregas (
    ID_Entrega INT IDENTITY(1,1) PRIMARY KEY,
    ID_Tarea INT NOT NULL FOREIGN KEY REFERENCES Tareas(ID_Tarea),
    ID_Estudiante INT NOT NULL FOREIGN KEY REFERENCES Estudiantes(ID_Estudiante),
    ArchivoURL VARCHAR(255) NOT NULL,
    FechaHoraEntrega DATETIME DEFAULT GETDATE(),
    Estado BIT DEFAULT 1
);

-- 9. Tabla Actividades
CREATE TABLE Actividades (
    ID_Actividad INT IDENTITY(1,1) PRIMARY KEY,
    ID_Grupo INT NOT NULL FOREIGN KEY REFERENCES Grupos(ID_Grupo),
    Titulo VARCHAR(150) NOT NULL,
    Categoria VARCHAR(50),
    FechaAsignacion DATETIME DEFAULT GETDATE(),
    FechaLimite DATETIME NOT NULL,
    PuntuacionMaxima DECIMAL(5,2),
    NumIntentos INT DEFAULT 1,
    Estado BIT DEFAULT 1
);

-- 10. Tabla Calificaciones
CREATE TABLE Calificaciones (
    ID_Calificacion INT IDENTITY(1,1) PRIMARY KEY,
    ID_Estudiante INT NOT NULL FOREIGN KEY REFERENCES Estudiantes(ID_Estudiante),
    ID_Tarea INT NULL FOREIGN KEY REFERENCES Tareas(ID_Tarea),
    ID_Actividad INT NULL FOREIGN KEY REFERENCES Actividades(ID_Actividad),
    Puntuacion DECIMAL(5,2) CHECK (Puntuacion >= 0 AND Puntuacion <= 100),
    Retroalimentacion TEXT,
    FechaCalificacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_Asignacion CHECK (
        (ID_Tarea IS NOT NULL AND ID_Actividad IS NULL) OR 
        (ID_Tarea IS NULL AND ID_Actividad IS NOT NULL)
    )
);

-- 11. Tabla Mensajes_Chat (Se conecta directamente con la tabla Usuarios)
CREATE TABLE Mensajes_Chat (
    ID_Mensaje INT IDENTITY(1,1) PRIMARY KEY,
    ID_Grupo INT NOT NULL FOREIGN KEY REFERENCES Grupos(ID_Grupo),
    ID_Remitente INT NOT NULL FOREIGN KEY REFERENCES Usuarios(ID_Usuario), 
    Texto TEXT NOT NULL,
    FechaHora DATETIME DEFAULT GETDATE(),
    Editado BIT DEFAULT 0,
    Estado BIT DEFAULT 1 
);