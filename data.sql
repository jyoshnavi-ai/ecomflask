-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: ecom29
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admindata`
--

DROP TABLE IF EXISTS `admindata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admindata` (
  `adminid` binary(16) NOT NULL,
  `adminname` varchar(50) NOT NULL,
  `adminemail` varchar(50) NOT NULL,
  `adminphone_no` varchar(10) DEFAULT NULL,
  `adminpassword` varbinary(255) NOT NULL,
  `adminaddress` varchar(255) NOT NULL,
  `adminfilename` varchar(15) DEFAULT NULL,
  `adminagree` enum('on','off') DEFAULT NULL,
  PRIMARY KEY (`adminid`),
  UNIQUE KEY `adminemail` (`adminemail`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admindata`
--

LOCK TABLES `admindata` WRITE;
/*!40000 ALTER TABLE `admindata` DISABLE KEYS */;
INSERT INTO `admindata` VALUES (_binary '!]o¡…²\ñŒP»µYK±','jyoshnavi','jyoshnavii.k@gmail.com',NULL,_binary '$2b$12$hWKKyD45M699edY7q3JchuAvIKNtf5vIpc3LtFMFxsIipei1uUIla','Deepa Towers , TF-1,12-201',NULL,'on');
/*!40000 ALTER TABLE `admindata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cart`
--

DROP TABLE IF EXISTS `cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cart` (
  `cartid` binary(16) NOT NULL,
  `userid` binary(16) NOT NULL,
  `itemid` binary(16) NOT NULL,
  `quantity` int NOT NULL DEFAULT '1',
  `added_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cartid`),
  KEY `userid` (`userid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`) ON DELETE CASCADE,
  CONSTRAINT `cart_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cart`
--

LOCK TABLES `cart` WRITE;
/*!40000 ALTER TABLE `cart` DISABLE KEYS */;
/*!40000 ALTER TABLE `cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `items` (
  `itemid` binary(16) NOT NULL,
  `itemname` longtext NOT NULL,
  `itemdescription` longtext,
  `itemAbout` longtext,
  `itemprice` decimal(10,2) DEFAULT NULL,
  `itemquantity` int unsigned DEFAULT NULL,
  `category` enum('home_appliances','grocery','electronics','sports','toys','fashion') DEFAULT NULL,
  `added_by` binary(16) DEFAULT NULL,
  `itemfilename` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`itemid`),
  KEY `added_by` (`added_by`),
  CONSTRAINT `items_ibfk_1` FOREIGN KEY (`added_by`) REFERENCES `admindata` (`adminid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES (_binary '¾\äOå…³\ñŒP»µYK±','gucci','Black Gg Marmon Small Crossbody Bag','Black gg small crossbody bag, zip closure, 1 compartment, inside slip pocket, metal logo, chevron pattern, adjustable crossbody strap. Country of Origin: Italy',120678.00,0,'fashion',_binary '!]o¡…²\ñŒP»µYK±','447282.jpg','2026-07-22 15:27:27');
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_item_details`
--

DROP TABLE IF EXISTS `order_item_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_item_details` (
  `orderdetails_id` int unsigned NOT NULL AUTO_INCREMENT,
  `orderid` int unsigned DEFAULT NULL,
  `itemid` binary(16) DEFAULT NULL,
  `item_name` longtext,
  `item_price` decimal(10,2) DEFAULT NULL,
  `item_quantity` int unsigned DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL,
  `item_category` enum('home_appliances','grocery','electronics','sports','toys','fashion') DEFAULT NULL,
  `item_filename` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`orderdetails_id`),
  KEY `orderid` (`orderid`),
  KEY `itemid` (`itemid`),
  CONSTRAINT `order_item_details_ibfk_1` FOREIGN KEY (`orderid`) REFERENCES `orders` (`orderid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `order_item_details_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`itemid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_item_details`
--

LOCK TABLES `order_item_details` WRITE;
/*!40000 ALTER TABLE `order_item_details` DISABLE KEYS */;
INSERT INTO `order_item_details` VALUES (1,1,_binary '¾\äOå…³\ñŒP»µYK±','gucci',120678.00,1,241356.00,'fashion','447282.jpg');
/*!40000 ALTER TABLE `order_item_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `orderid` int unsigned NOT NULL AUTO_INCREMENT,
  `razorpay_orderid` varchar(100) DEFAULT NULL,
  `razorpay_paymentid` varchar(100) DEFAULT NULL,
  `userid` binary(16) DEFAULT NULL,
  `total_amount` decimal(10,2) DEFAULT NULL,
  `grand_total` decimal(10,2) DEFAULT NULL,
  `delivery` int unsigned DEFAULT '40',
  `tax` decimal(10,2) DEFAULT NULL,
  `status` varchar(30) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`orderid`),
  KEY `userid` (`userid`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdata` (`userid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,'order_TGsfbxzknVTxax','pay_TGsgJaBCpfFsLm',_binary '\ï\îƒ…³\ñŒP»µYK±',120678.00,126751.90,40,6033.90,'paid','2026-07-23 14:09:07');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userdata`
--

DROP TABLE IF EXISTS `userdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userdata` (
  `userid` binary(16) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `useremail` varchar(50) DEFAULT NULL,
  `password` varbinary(255) DEFAULT NULL,
  `useraddress` text,
  `usergender` enum('male','female','woke') DEFAULT NULL,
  `userphone` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userdata`
--

LOCK TABLES `userdata` WRITE;
/*!40000 ALTER TABLE `userdata` DISABLE KEYS */;
INSERT INTO `userdata` VALUES (_binary '\ï\îƒ…³\ñŒP»µYK±','jyoshnavi','jyoshnavii.k@gmail.com',_binary '$2b$12$kFfZZb.RjDwnBamTLFhgNudzifwvWJ4oK99Q1JQYPP9LELmPccCcG','Deepa Towers , TF-1,12-201','female','09032676299');
/*!40000 ALTER TABLE `userdata` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-23 16:05:15
