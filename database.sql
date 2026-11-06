-- ====================================================================
-- DISASTERSYNC AI - DATABASE SCHEMA
-- AI-Powered Multi-Agent Disaster Response and Emergency Coordination System
-- Project Code: AG-AI-01 | Bapatla Women's Engineering College
-- Team: K. Mrudhula Reddy, G. Kavya, T. Sneha Latha
-- ====================================================================

CREATE DATABASE IF NOT EXISTS `disastersync_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `disastersync_db`;

-- 1. INCIDENTS TABLE
CREATE TABLE IF NOT EXISTS `incidents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `incident_code` VARCHAR(30) NOT NULL UNIQUE,
    `emergency_type` VARCHAR(50) NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT NOT NULL,
    `location_address` VARCHAR(255) NOT NULL,
    `landmark` VARCHAR(255) DEFAULT '',
    `latitude` DECIMAL(10, 7) NOT NULL,
    `longitude` DECIMAL(10, 7) NOT NULL,
    `urgency_level` ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW') NOT NULL DEFAULT 'MEDIUM',
    `urgency_score` INT NOT NULL DEFAULT 50,
    `urgency_reasons` TEXT,
    `people_affected` INT DEFAULT 0,
    `trapped_count` INT DEFAULT 0,
    `injured_count` INT DEFAULT 0,
    `status` ENUM('Reported', 'Verified', 'Dispatched', 'In Progress', 'Resolved', 'Closed') NOT NULL DEFAULT 'Reported',
    `is_sos` BOOLEAN NOT NULL DEFAULT FALSE,
    `is_duplicate` BOOLEAN NOT NULL DEFAULT FALSE,
    `parent_incident_id` INT DEFAULT NULL,
    `reporter_name` VARCHAR(100) DEFAULT 'Anonymous Citizen',
    `reporter_email` VARCHAR(120) DEFAULT NULL,
    `reporter_contact` VARCHAR(50) DEFAULT 'Simulated Contact',
    `source` VARCHAR(50) DEFAULT 'Citizen Mobile Form',
    `confidence_score` DECIMAL(4, 2) DEFAULT 0.90,
    `photo_url` VARCHAR(500) DEFAULT NULL,
    `reported_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_status` (`status`),
    INDEX `idx_urgency` (`urgency_level`),
    INDEX `idx_type` (`emergency_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. AGENT RECOMMENDATIONS TABLE
CREATE TABLE IF NOT EXISTS `agent_recommendations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `incident_id` INT NOT NULL,
    `agent_name` VARCHAR(60) NOT NULL,
    `recommendation_text` TEXT NOT NULL,
    `priority_level` VARCHAR(30) DEFAULT 'Normal',
    `suggested_actions` TEXT,
    `evidence_refs` TEXT,
    `confidence` DECIMAL(4, 2) DEFAULT 0.85,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`incident_id`) REFERENCES `incidents`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. SIMULATED ALERTS TABLE
CREATE TABLE IF NOT EXISTS `simulated_alerts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `incident_id` INT NOT NULL,
    `agency_type` VARCHAR(50) NOT NULL,
    `agency_name` VARCHAR(100) NOT NULL,
    `alert_channel` VARCHAR(50) NOT NULL,
    `alert_title` VARCHAR(255) NOT NULL,
    `alert_message` TEXT NOT NULL,
    `status` ENUM('PENDING_APPROVAL', 'APPROVED', 'DISPATCHED', 'ACKNOWLEDGED', 'EN_ROUTE', 'ON_SCENE') DEFAULT 'PENDING_APPROVAL',
    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `acknowledged_at` DATETIME DEFAULT NULL,
    `officer_approved_by` VARCHAR(100) DEFAULT NULL,
    FOREIGN KEY (`incident_id`) REFERENCES `incidents`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. RESOURCES INVENTORY TABLE
CREATE TABLE IF NOT EXISTS `resources` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `agency_id` VARCHAR(50) NOT NULL,
    `resource_name` VARCHAR(120) NOT NULL,
    `resource_type` VARCHAR(60) NOT NULL,
    `total_capacity` INT NOT NULL DEFAULT 1,
    `available_capacity` INT NOT NULL DEFAULT 1,
    `base_location` VARCHAR(150) NOT NULL,
    `latitude` DECIMAL(10, 7) NOT NULL,
    `longitude` DECIMAL(10, 7) NOT NULL,
    `status` VARCHAR(50) DEFAULT 'Available',
    `last_updated` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `incident_id` INT DEFAULT NULL,
    `actor_name` VARCHAR(100) NOT NULL,
    `actor_role` VARCHAR(60) NOT NULL,
    `action_type` VARCHAR(60) NOT NULL,
    `details` TEXT NOT NULL,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. EMAIL NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS `email_notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `incident_id` INT NOT NULL,
    `recipient_email` VARCHAR(255) NOT NULL,
    `subject` VARCHAR(255) NOT NULL,
    `notification_type` VARCHAR(50) NOT NULL,
    `old_status` VARCHAR(50) DEFAULT NULL,
    `new_status` VARCHAR(50) DEFAULT NULL,
    `status` VARCHAR(50) NOT NULL,
    `error_message` TEXT DEFAULT NULL,
    `sent_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `dedup_key` VARCHAR(255) UNIQUE,
    FOREIGN KEY (`incident_id`) REFERENCES `incidents`(`id`) ON DELETE CASCADE,
    INDEX `idx_dedup` (`dedup_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- SEED DATA: EMERGENCY RESOURCES
-- ====================================================================
INSERT INTO `resources` (`agency_id`, `resource_name`, `resource_type`, `total_capacity`, `available_capacity`, `base_location`, `latitude`, `longitude`, `status`) VALUES
('police', 'Rapid Response Patrol Unit Alpha', 'Police Vehicle', 4, 3, 'Central Police Station', 15.9054, 80.4682, 'Available'),
('police', 'Traffic & Perimeter Control Unit 3', 'Police Squad', 6, 5, 'North Bypass Checkpost', 15.9180, 80.4590, 'Available'),
('fire', 'Heavy Water Tender & Foam Truck #1', 'Fire Engine', 2, 2, 'Main Fire Station HQ', 15.9010, 80.4720, 'Available'),
('fire', 'Rescue Boat & Hydraulic Cutter Unit #1', 'Flood & Rescue Boat', 3, 2, 'Riverbank Emergency Depot', 15.8920, 80.4850, 'Available'),
('fire', 'Hydraulic Aerial Ladder Truck (50m)', 'Fire Equipment', 1, 1, 'Main Fire Station HQ', 15.9010, 80.4720, 'Available'),
('medical', 'Advanced Life Support (ALS) Ambulance #1', 'Ambulance', 3, 2, 'General District Hospital', 15.9120, 80.4620, 'Available'),
('medical', 'Basic Life Support (BLS) Ambulance #2', 'Ambulance', 2, 1, 'Community Health Center', 15.9220, 80.4480, 'Available'),
('medical', 'Emergency Trauma & ICU Ward Beds', 'Hospital ICU Beds', 20, 14, 'General District Hospital', 15.9120, 80.4620, 'Available'),
('rescue', 'NDRF Urban Search & Rescue Battalion (USAR-1)', 'Rescue Team', 15, 12, 'State Disaster Response Base', 15.8850, 80.4750, 'Available'),
('rescue', 'Inflatable Motorized Rescue Boats Fleet', 'Rescue Craft', 6, 4, 'Coastal Relief Outpost', 15.8790, 80.4910, 'Available');

-- ====================================================================
-- SEED DATA: AUDIT LOG ENTRY
-- ====================================================================
INSERT INTO `audit_logs` (`incident_id`, `actor_name`, `actor_role`, `action_type`, `details`) VALUES
(NULL, 'System Init', 'System Administrator', 'SYSTEM_INITIALIZED', 'DisasterSync AI database initialized with sample agencies and resource stocks.');

