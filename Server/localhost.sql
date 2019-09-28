-- phpMyAdmin SQL Dump
-- version 4.6.6deb4
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 05. Sep 2019 um 22:34
-- Server-Version: 10.1.37-MariaDB-0+deb9u1
-- PHP-Version: 7.0.33-0+deb9u3

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `CoSESWeather_DB`
--
CREATE DATABASE IF NOT EXISTS `CoSESWeather_DB` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `CoSESWeather_DB`;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `admin_log`
--

CREATE TABLE `admin_log` (
  `id` int(10) UNSIGNED NOT NULL,
  `user` varchar(64) NOT NULL,
  `action` varchar(128) NOT NULL,
  `reason` varchar(128) NOT NULL,
  `priority` tinyint(1) NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `sensor_datasets`
--

CREATE TABLE `sensor_datasets` (
  `id` int(10) UNSIGNED NOT NULL,
  `temp` float DEFAULT NULL,
  `wind` float DEFAULT NULL,
  `spn1_radTot` float DEFAULT NULL,
  `spn1_radDiff` float DEFAULT NULL,
  `spn1_sun` tinyint(1) DEFAULT NULL,
  `rad_cmp1` float DEFAULT NULL,
  `rad_cmp2` float DEFAULT NULL,
  `rad_cmp3` float DEFAULT NULL,
  `t_unix` int(10) UNSIGNED NOT NULL,
  `archived` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `users`
--

CREATE TABLE `users` (
  `id` int(10) UNSIGNED NOT NULL,
  `user` varchar(64) NOT NULL,
  `pass` char(40) NOT NULL,
  `salt` char(16) NOT NULL,
  `admin` tinyint(1) NOT NULL,
  `email` varchar(128) NOT NULL,
  `lastLogin` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `admin_log`
--
ALTER TABLE `admin_log`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `sensor_datasets`
--
ALTER TABLE `sensor_datasets`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `admin_log`
--
ALTER TABLE `admin_log`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `sensor_datasets`
--
ALTER TABLE `sensor_datasets`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `users`
--
ALTER TABLE `users`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
