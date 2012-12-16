CREATE DATABASE CHSWDATA;
USE CHSWDATA;
CREATE TABLE IntraDayQuotation
(
	Symbol    CHAR(20) NOT NULL,
	TradeTime DATETIME NOT NULL,
	TradePx	  FLOAT NOT NULL,
	OpenPx	  FLOAT NOT NULL,
	TradeShare INT NOT NULL,
	TradeVolumn DOUBLE NOT NULL,
	TradeType ENUM('BUY','SELL','NETURAL') NOT NULL,
	INDEX( TradeTime, Symbol ),
	INDEX( Symbol, TradeTime )
)ENGINE = InnoDB;

CREATE TABLE DayQuotation
(
	Symbol    CHAR(20) NOT NULL,
	TradeTime DATE NOT NULL,
	OpenPx	  FLOAT NOT NULL,
	ClosePx   FLOAT NOT NULL,
	HighPx    FLOAT NOT NULL,
	LowPx     FLOAT NOT NULL,
	TradeShare INT NOT NULL,
	TradeVolumn DOUBLE NOT NULL,
	TurnOverRate FLOAT NOT NULL,
	INDEX(Symbol,TradeTime),
	INDEX(TradeTime,Symbol)
)ENGINE = InnoDB;

CREATE TABLE OHLCQuotation
(
	Symbol    CHAR(20) NOT NULL,
	StartTime DATETIME NOT NULL,
	EndTime DATETIME NOT NULL,
	OpenPx	  FLOAT NOT NULL,
	ClosePx   FLOAT NOT NULL,
	HighPx    FLOAT NOT NULL,
	LowPx     FLOAT NOT NULL,
	Mean	  FLOAT NOT NULL,
	Var  	  FLOAT NOT NULL,
	TradeShare INT NOT NULL,
	TradeVolumn DOUBLE NOT NULL,
	INDEX( StartTime, EndTime, Symbol ),
	INDEX( Symbol, StartTime, EndTime )
)ENGINE = InnoDB;
