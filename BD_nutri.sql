DROP DATABASE IF EXISTS sistemaNutricional;

CREATE DATABASE sistemaNutricional;
USE sistemaNutricional;

-- 1. USUARIOS 
CREATE TABLE Usuarios (
    id_usuario INT IDENTITY (1,1) PRIMARY KEY NOT NULL,
    nombre_usuario VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,  
    preferencias_usuario VARCHAR(255) NULL,
    rol_usuario VARCHAR(20) NOT NULL CONSTRAINT df_usuarios_rol DEFAULT 'usuario',
    email_usuario VARCHAR(120) NULL,
    edad_usuario INT NULL,
    peso_kg FLOAT NULL,
    altura_cm FLOAT NULL,
    telefono_usuario VARCHAR(12) NULL,
    CONSTRAINT uq_usuarios_nombre UNIQUE (nombre_usuario),
    CONSTRAINT ck_usuarios_rol CHECK (rol_usuario IN ('usuario','doctor','admin'))
);

-- 2. OBJETIVOS NUTRICIONALES 
CREATE TABLE ObjetivosNutricionales (
    id_objetivos INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    calorias_meta FLOAT NOT NULL,   -- kcal diarias
    proteina_meta FLOAT NOT NULL,   -- g diarios
    id_usuario INT   NOT NULL,
    CONSTRAINT uq_objetivo_usuario UNIQUE (id_usuario),
    CONSTRAINT fk_objetivo_usuario FOREIGN KEY (id_usuario)
        REFERENCES Usuarios (id_usuario) ON DELETE CASCADE,
    CONSTRAINT ck_objetivo_cal  CHECK (calorias_meta > 0),
    CONSTRAINT ck_objetivo_prot CHECK (proteina_meta > 0)
);

-- 3. CATÁLOGO DE ALIMENTOS 
CREATE TABLE catalogo_alimentos (
    id_alimento INT IDENTITY (1,1) PRIMARY KEY NOT NULL,
    nombre_alimento VARCHAR(100) NOT NULL,
    tipo_factory VARCHAR(50) NOT NULL,      -- Proteina, Fruta, Verdura y Leguminosa
    calorias FLOAT NOT NULL DEFAULT 0,   
    proteina FLOAT NOT NULL DEFAULT 0,   
    carbohidratos FLOAT NOT NULL DEFAULT 0,   
    grasas FLOAT NOT NULL DEFAULT 0,   
    azucar FLOAT NOT NULL DEFAULT 0,   
    sodio FLOAT NOT NULL DEFAULT 0,  
    CONSTRAINT uq_catalogo_nombre UNIQUE (nombre_alimento),
    CONSTRAINT ck_catalogo_grupo CHECK (tipo_factory IN ('Proteina','Fruta','Verdura','Leguminosa')),
    CONSTRAINT ck_catalogo_nutr  CHECK (calorias >= 0 AND proteina >= 0 AND carbohidratos >= 0 AND grasas >= 0 AND azucar >= 0 AND sodio >= 0)
);

-- 4. REGISTROS DE CONSUMO (historial) 
CREATE TABLE registros_consumo (
    id_consumo INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    id_usuario INT NOT NULL,
    fecha DATETIME NOT NULL DEFAULT GETDATE(),
    nombre_consumido VARCHAR(150) NOT NULL,              
    ingredientes_consumidos VARCHAR(500) NULL DEFAULT '',
    calorias_totales FLOAT NOT NULL,
    proteina_total FLOAT NOT NULL,
    carbohidratos_total FLOAT NOT NULL,
    grasas_total FLOAT NOT NULL,
    azucar_total FLOAT NOT NULL,
    sodio_total FLOAT NOT NULL,
    CONSTRAINT fk_registro_usuario FOREIGN KEY (id_usuario)
        REFERENCES Usuarios (id_usuario) ON DELETE CASCADE
);

CREATE INDEX idx_registro_usuario_fecha ON registros_consumo (id_usuario, fecha);

-- 5. SOLICITUDES DE AYUDA 
CREATE TABLE solicitudes_ayuda (
    id_solicitudes INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    paciente_id INT NOT NULL,
    doctor_id INT NULL,
    motivo VARCHAR(300) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    fecha_creacion DATETIME NOT NULL DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT fk_solicitud_paciente FOREIGN KEY (paciente_id)
        REFERENCES Usuarios (id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_solicitud_doctor FOREIGN KEY (doctor_id)
        REFERENCES Usuarios (id_usuario),
    CONSTRAINT ck_solicitud_estado CHECK (estado IN ('pendiente','en_atencion','cerrada'))
);

CREATE INDEX idx_solicitud_paciente ON solicitudes_ayuda (paciente_id);
CREATE INDEX idx_solicitud_doctor_estado ON solicitudes_ayuda (doctor_id, estado);

-- 6. MENSAJES DEL CHAT 
CREATE TABLE mensajes_chat (
    id_mensaje INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    solicitud_id INT NOT NULL,
    remitente_id INT NOT NULL,
    contenido VARCHAR(MAX) NOT NULL,
    fecha_envio DATETIME NOT NULL DEFAULT GETDATE(),
    leido BIT NOT NULL DEFAULT 0,
    CONSTRAINT fk_mensaje_solicitud FOREIGN KEY (solicitud_id)
        REFERENCES solicitudes_ayuda (id_solicitudes) ON DELETE CASCADE,
    CONSTRAINT fk_mensaje_remitente FOREIGN KEY (remitente_id)
        REFERENCES Usuarios (id_usuario)
);

-- VISTA: resumen diario contra la meta 
CREATE VIEW v_resumen_diario AS
SELECT
    iu.id_usuario,
    u.nombre_usuario AS usuario,
    CAST(iu.fecha AS DATE) AS dia,
    COUNT(*) AS num_registros,
    ROUND(SUM(iu.calorias_totales), 1) AS calorias,
    ROUND(SUM(iu.proteina_total), 1) AS proteina,
    ROUND(SUM(iu.carbohidratos_total), 1) AS carbohidratos,
    ROUND(SUM(iu.grasas_total), 1) AS grasas,
    ROUND(SUM(iu.azucar_total), 1) AS azucar,
    ROUND(SUM(iu.sodio_total), 1) AS sodio,
    o.calorias_meta,
    o.proteina_meta,
    ROUND(100 * SUM(iu.calorias_totales) / o.calorias_meta, 1) AS pct_calorias_meta
FROM registros_consumo iu JOIN Usuarios u ON u.id_usuario = iu.id_usuario LEFT JOIN ObjetivosNutricionales o ON o.id_usuario = iu.id_usuario
GROUP BY iu.id_usuario, u.nombre_usuario, CAST(iu.fecha AS DATE), o.calorias_meta, o.proteina_meta;

-- Solicitudes con nombre de paciente, doctor y número de mensajes (panel del doctor / admin)
CREATE VIEW v_solicitudes_detalle AS
SELECT
    s.id_solicitudes,               
    s.estado,
    s.motivo,
    p.nombre_usuario AS paciente,
    d.nombre_usuario AS doctor,
    s.fecha_creacion,
    s.fecha_actualizacion,
    (SELECT COUNT(*) FROM mensajes_chat m WHERE m.solicitud_id = s.id_solicitudes) AS total_mensajes,
    (SELECT COUNT(*) FROM mensajes_chat m WHERE m.solicitud_id = s.id_solicitudes AND m.leido = 0) AS mensajes_sin_leer
FROM solicitudes_ayuda s INNER JOIN Usuarios p ON p.id_usuario = s.paciente_id LEFT JOIN Usuarios d ON d.id_usuario = s.doctor_id;

-- DATOS INICIALES
-- Cuentas de prueba:  Armando / 123456 (usuario) | doctor / doctor123 (doctor) | admin / admin123 (admin)
INSERT INTO Usuarios (nombre_usuario, password_hash, rol_usuario, preferencias_usuario, email_usuario, edad_usuario, peso_kg, altura_cm, telefono_usuario) VALUES
    ('Armando', 'scrypt:32768:8:1$qs6jPFIwb1W55M8Q$3643c04c1a2bf8f58aa035b4eacaf903ce548fa730e5c1146a88de77a484ccf6596a2099132a7b7544ea3a74f023a82ca37b8353f66b2dd5d8e6631832e3f540', 'usuario', N'Hipertrofia muscular, comida alta en proteína', 'armando@nutri.com', 22, 74.5, 176.0, '555-123-4567'),
    ('admin',   'scrypt:32768:8:1$NA9mdyYMiDObVEwz$ebc52af2238bff0638e03a9152fd41cf5622808ea62998777f17c352f73f39308a208da0bf150769a5e45120f75dc439138823a988511fe8219f88c4374973ba',   'admin',   N'Administración del sistema', 'admin@nutri.com', 30, NULL, NULL, '555-000-0001'),
    ('doctor',  'scrypt:32768:8:1$5TxYC3yuZIAuF5JA$cd17efc723736518abd5b95c5420f0235ece53d24170edc00548a466283a57cb98925b9a47ae1cdafcac308414020c0d08316813ffc0917336a89e320c863dd0',  'doctor',  N'Nutrición clínica y deportiva', 'doctor@nutri.com', 35, NULL, NULL, '555-000-0002');

INSERT INTO ObjetivosNutricionales (calorias_meta, proteina_meta, id_usuario) VALUES (2500.0, 160.0, 1);

INSERT INTO catalogo_alimentos
    (nombre_alimento, tipo_factory, calorias, proteina, carbohidratos, grasas, azucar, sodio) VALUES
    ('Pechuga de Pollo (100g)', 'Proteina', 165.0, 31.0, 0.0, 3.6, 0.0, 74.0),
    ('Plátano', 'Fruta', 105.0, 1.3, 27.0, 0.3, 14.0, 1.0),
    ('Brócoli (1 taza)', 'Verdura', 55.0, 3.7, 11.2, 0.6, 2.0, 33.0),
    ('Tofu', 'Proteina', 150.0, 25.0, 0.0, 5.0, 0.0, 50.0),
    ('Jitomate', 'Verdura', 30.0, 2.0, 5.0, 0.0, 2.0, 10.0);

INSERT INTO registros_consumo (id_usuario, fecha, nombre_consumido, ingredientes_consumidos,calorias_totales, proteina_total, carbohidratos_total, grasas_total, azucar_total, sodio_total) VALUES
    (1, '2026-11-16T22:29:02', 'Pechuga de Pollo (100g)', '', 165.0, 31.0, 0.0, 3.6, 0.0, 74.0),
    (1, '2026-11-16T22:31:52', 'Comida Estándar', '', 325.0, 36.0, 38.2, 4.5, 16.0, 108.0),
    (1, '2026-11-16T22:32:24', 'Comida Estándar (Vegano)', '', 160.0, 5.0, 38.2, 0.9, 16.0, 34.0),
    (1, '2026-11-16T22:35:44', 'Pechuga de Pollo (100g)', '', 165.0, 31.0, 0.0, 3.6, 0.0, 74.0),
    (1, '2026-11-16T23:43:20', 'Tofu', '', 150.0, 25.0, 0.0, 5.0, 0.0, 50.0),
    (1, '2026-11-17T20:03:03', 'Comida Estándar', '', 220.0, 34.7, 11.2, 4.2, 2.0, 107.0),
    (1, '2026-11-17T20:04:30', 'Jitomate', '', 30.0, 2.0, 5.0, 0.0, 2.0, 10.0),
    (1, '2026-11-18T01:23:32', 'Desayuno Estándar', 'Pechuga de Pollo (100g), Plátano, Tofu', 420.0, 57.3, 27.0, 8.9, 14.0, 125.0),
    (1, '2026-11-18T01:35:01', 'Brócoli (1 taza) (100g)', '', 55.0, 3.7, 11.2, 0.6, 2.0, 33.0),
    (1, '2026-11-18T01:35:15', 'Brócoli (1 taza) (150g)', '', 82.5, 5.6, 16.8, 0.9, 3.0, 49.5),
    (1, '2026-11-18T02:20:58', 'Comida', 'Brócoli (1 taza) (100g), Jitomate (100g)', 85.0, 5.7, 16.2, 0.6, 4.0, 43.0);

-- Una solicitud de ayuda de ejemplo con su chat
INSERT INTO solicitudes_ayuda (paciente_id, doctor_id, motivo, estado) VALUES (1, 3, 'Quiero ajustar mi dieta para ganar masa muscular', 'en_atencion');

INSERT INTO mensajes_chat (solicitud_id, remitente_id, contenido, leido) VALUES
    (1, 1, 'Quiero ajustar mi dieta para ganar masa muscular', 1),
    (1, 3,  'Hola Armando, revisé tu historial. ¿Cuántas comidas haces al día?', 1),
    (1, 1, 'Tres comidas y una merienda.', 0);

-- CONSULTAS DE EJEMPLO
-- 1) Usuarios por rol
SELECT rol_usuario, COUNT(*) AS total FROM Usuarios GROUP BY rol_usuario;

-- 2) Solicitudes pendientes sin doctor asignado
SELECT * FROM v_solicitudes_detalle WHERE estado = 'pendiente' AND doctor IS NULL;

-- 3) Pacientes que atiende el doctor 'doctor' (con total de registros de consumo)
SELECT p.nombre_usuario AS paciente, s.estado, COUNT(DISTINCT r.id_consumo) AS registros_consumo
FROM solicitudes_ayuda s INNER JOIN Usuarios d ON d.id_usuario = s.doctor_id AND d.nombre_usuario = N'doctor'
INNER JOIN Usuarios p ON p.id_usuario = s.paciente_id
LEFT JOIN registros_consumo r ON r.id_usuario = p.id_usuario
GROUP BY p.nombre_usuario, s.estado;

-- 4) Resumen diario de calorías contra la meta
SELECT * FROM v_resumen_diario ORDER BY dia;

-- 5) Mensajes sin leer por solicitud
SELECT id_solicitud, paciente, doctor, mensajes_sin_leer FROM v_solicitudes_detalle WHERE mensajes_sin_leer > 0;
