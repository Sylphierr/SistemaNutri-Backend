DROP DATABASE IF EXISTS sistemanutri;

CREATE DATABASE sistemanutri;
USE sistemanutri;

-- 1. USUARIOS 
CREATE TABLE Usuarios (
    id_usuario INT IDENTITY (1,1) PRIMARY KEY NOT NULL,
    nombre_usuario VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,  
    preferencias_usuario VARCHAR(255) NULL,
    CONSTRAINT uq_usuarios_nombre UNIQUE (nombre_usuario)
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
    ingredientes_consumidos NVARCHAR(500) NULL DEFAULT '',
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

-- DATOS INICIALES
-- Usuario de prueba: Armando / contraseña 123456
INSERT INTO Usuarios (nombre_usuario, preferencias_usuario, password_hash) VALUES ('Armando', 'Hipertrofia muscular, comida alta en proteína', 'scrypt:32768:8:1$qs6jPFIwb1W55M8Q$3643c04c1a2bf8f58aa035b4eacaf903ce548fa730e5c1146a88de77a484ccf6596a2099132a7b7544ea3a74f023a82ca37b8353f66b2dd5d8e6631832e3f540');

INSERT INTO ObjetivosNutricionales (calorias_meta, proteina_meta, id_usuario) VALUES (2500.0, 160.0, 1);

INSERT INTO catalogo_alimentos (nombre_alimento, tipo_factory, calorias, proteina, carbohidratos, grasas, azucar, sodio) VALUES
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

-- Comprobación 

SELECT * FROM Usuarios;
SELECT * FROM ObjetivosNutricionales;
SELECT * FROM catalogo_alimentos;
SELECT * FROM registros_consumo;
SELECT * FROM v_resumen_diario;