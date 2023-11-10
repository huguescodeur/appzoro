CREATE TABLE Produit (
IdProduit INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
NomProduit VARCHAR(20),
CatProduit VARCHAR(20),
PrixUnitaire FLOAT
);

CREATE TABLE Magasin(
IdMagasin INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
NomMagasin VARCHAR(20),
AdresseMagasin VARCHAR(50),
Telephone VARCHAR(16),
mail VARCHAR(20)
);
    
CREATE TABLE Stock (
Idstock INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
Quantitestock INT ,
IdProduit INT NOT NULL,
IdMagasin INT NOT NULL,
FOREIGN KEY  (IdProduit) REFERENCES Produit (IdProduit),
FOREIGN KEY (IdMagasin) REFERENCES Magasin (IdMagasin)
);

CREATE TABLE Vente (
IdVente INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
Quantitevendu INT ,
Prixtotal FLOAT,
Datevente DATE,
IdProduit INT NOT NULL,
IdMagasin INT NOT NULL,
FOREIGN KEY  (IdProduit) REFERENCES Produit (IdProduit),
FOREIGN KEY (IdMagasin) REFERENCES Magasin (IdMagasin)
)