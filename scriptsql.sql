USE AlgeVisual;
GO

delete from Usuarios where ID_Usuario = 1; -- Elimina los usuarios de prueba excepto el administrador

INSERT INTO Usuarios (Matricula, NombreCompleto, Correo, Contrasena, Rol, Estado)
VALUES ('ADMIN-01', 'Administrador', 'admin@algevisual.com', '12345', 'Administrador', 1);