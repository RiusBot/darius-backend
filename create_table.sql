
-- referral
CREATE TABLE `referral` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT UNIQUE,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    `referrer_id` INT(11),
    `referral_code` varchar(8) UNIQUE NOT NULL,
    `register_count` int(11) NOT NULL  DEFAULT 0,
    `bot_count` int(11) NOT NULL  DEFAULT 0,
    `subscribe_count` int(11) NOT NULL  DEFAULT 0,
    `total_rebate` DOUBLE NOT NULL DEFAULT 0,
    `rebate_rate` DOUBLE NOT NULL DEFAULT 0.1,
    `referrer_rebate_rate` DOUBLE NOT NULL DEFAULT 0.1,
    `referral_rebate_rate` DOUBLE NOT NULL DEFAULT 0,
    KEY (`user_id`),
    KEY (`is_del`),
    KEY (`referrer`),
    KEY (`referral_code`),
    CONSTRAINT FOREIGN KEY(`user_id`) REFERENCES `user`(id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(`referrer_id`) REFERENCES `referral`(id)
) CHARACTER SET utf8;

-- referral history
CREATE TABLE `referral_history` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    `rebate` DOUBLE NOT NULL DEFAULT 0,
    `referrer_id` INT(11) NOT NULL,
    `referral_id` INT(11) NOT NULL,
    `bot_id` INT(11) UNIQUE,
    `subscription_id` INT(11) UNIQUE,
    `referrer_rebate_rate` DOUBLE NOT NULL DEFAULT 0.1,
    `referral_rebate_rate` DOUBLE NOT NULL DEFAULT 0,
    KEY (`is_del`),
    KEY (`bot_id`),
    KEY (`referrer_id`),
    KEY (`referral_id`),
    KEY (`subscription_id`),
    CONSTRAINT FOREIGN KEY(`referrer_id`) REFERENCES `referral`(id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(`referral_id`) REFERENCES `referral`(id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(`bot_id`) REFERENCES `bot_order`(id) ON DELETE CASCADE,
    CONSTRAINT FOREIGN KEY(`subscription_id`) REFERENCES `subscription`(id) ON DELETE CASCADE
) CHARACTER SET utf8;


-- permission
CREATE TABLE `permission` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `role_id` int(11),
    `service` varchar(50) NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`role_id`),
    KEY (`is_del`),
    CONSTRAINT FOREIGN KEY(`role_id`) REFERENCES `role`(id) ON DELETE CASCADE
) CHARACTER SET utf8;

-- role
CREATE TABLE `role` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` varchar(50) UNIQUE NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`name`),
    KEY (`is_del`)
) CHARACTER SET utf8;


-- user
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `user_name` varchar(16),
  `email` varchar(32) UNIQUE,
  `uid` varchar(28) UNIQUE NOT NULL,
  `role_id` int(11) NOT NULL,
  `balance` DOUBLE NOT NULL DEFAULT 0,
  `referrer` varchar(8),
  `referral_code` varchar(8) UNIQUE NOT NULL,
  `referrer_count` int(11) NOT NULL  DEFAULT 0,
  `referral_id` int(11) UNIQUE,
  `is_del` BOOLEAN NOT NULL DEFAULT False,
   KEY (`user_name`),
   KEY (`email`),
   KEY (`created_at`),
   KEY (`uid`),
   KEY (`referrer`),
   KEY (`referral_code`),
   KEY (`is_del`),
   CONSTRAINT FOREIGN KEY (`role_id`) REFERENCES `role`(`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- telegram
CREATE TABLE IF NOT EXISTS `telegram` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `telegram_id` INT UNIQUE NOT NULL,
    `user_id` INT UNIQUE NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`user_id`),
    KEY (`telegram_id`),
    KEY (`created_at`),
    KEY (`is_del`),
    FOREIGN KEY(user_id) REFERENCES user(id)
) CHARACTER SET utf8;

-- plan
CREATE TABLE `plan` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `price` decimal(19, 4) NOT NULL,
  `day` decimal(10, 0) NOT NULL, -- should modify the term, available_day
  `name` varchar(50) UNIQUE NOT NULL,
  `channel` varchar(50) NOT NULL,
  `is_del` BOOLEAN NOT NULL DEFAULT False,
  KEY (`name`),
  KEY (`created_at`),
  KEY (`channel`),
  KEY (`is_del`),
  CHECK(day >= 0),
  CHECK(price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- subscription
CREATE TABLE `subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `user_id` int(11) NOT NULL,
  `plan_id` int(11) NOT NULL,
  `expire_date` DATETIME(6),
  `channel` varchar(50) NOT NULL,
  `invite_link` varchar(50) UNIQUE,
  `is_del` BOOLEAN DEFAULT False,
  KEY (`user_id`),
  KEY (`plan_id`),
  KEY (`expire_date`),
  KEY (`channel`),
  KEY (`is_del`),
  UNIQUE KEY `user_channel` (`user_id`, `channel`,`is_del`),
  CONSTRAINT FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  CONSTRAINT FOREIGN KEY (`plan_id`) REFERENCES `plan`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- transaction
CREATE TABLE `transaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `user_id` int(11) NOT NULL,
  `wallet` varchar(128) NOT NULL,
  `txid` varchar(128) UNIQUE NOT NULL,
  `date` DATETIME(6) NOT NULL,
  `amount` DOUBLE NOT NULL,
  `is_del` BOOLEAN NOT NULL DEFAULT False,
  KEY (`user_id`),
  KEY (`txid`),
  KEY (`wallet`),
  KEY (`date`),
  KEY (`is_del`),
  CONSTRAINT FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- api
CREATE TABLE `api` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` int(11) NOT NULL,
    `api_key` varchar(64) NOT NULL,
    `api_secret` varchar(400) NOT NULL,
    `password` varchar(64),
    `exchange` varchar(16) NOT NULL,
    `subaccount` varchar(32),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`user_id`),
    KEY (`exchange`),
    KEY (`is_del`),
    UNIQUE KEY `api_cred` (`api_key`,`api_secret`),
    CONSTRAINT FOREIGN KEY(`user_id`) REFERENCES `user`(id)
) CHARACTER SET utf8;

-- pair
CREATE TABLE `pair` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` int(11) NOT NULL,
    `name` varchar(64) NOT NULL,
    `types` varchar(16) NOT NULL,
    `lists` LONGTEXT NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`user_id`),
    KEY (`type`),
    KEY (`name`),
    KEY (`is_del`),
    UNIQUE KEY `user_name` (`user_id`,`name`),
    CONSTRAINT FOREIGN KEY(`user_id`) REFERENCES `user`(id)
) CHARACTER SET utf8;

-- bot order
CREATE TABLE IF NOT EXISTS `bot_order` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `channel` VARCHAR(32) NOT NULL,
    `status` VARCHAR(16) NOT NULL,
    `config_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `is_trial` BOOLEAN  DEFAULT FALSE  NOT NULL,
    `trial_expired_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`user_id`),
    KEY (`status`),
    KEY (`channel`),
    KEY (`created_at`),
    KEY (`config_id`),
    KEY (`is_trial`),
    KEY (`is_del`),
    KEY (`trial_expired_at`),
    FOREIGN KEY(user_id) REFERENCES user(id)
) CHARACTER SET utf8;


-- bot config
CREATE TABLE IF NOT EXISTS `bot_config` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `bot_id` INT,
    `api_id` INT NOT NULL,
    `pair_id` INT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `test` BOOLEAN  DEFAULT FALSE  NOT NULL,
    `hyperopt` BOOLEAN  DEFAULT FALSE  NOT NULL,
    `target` VARCHAR(16) NOT NULL,
    `quantity` DOUBLE NOT NULL,
    `leverage` DOUBLE NOT NULL DEFAULT 1,
    `stop_loss` DOUBLE,
    `take_profit` DOUBLE,
    `order_type` VARCHAR(16) NOT NULL   DEFAULT 'MARKET',
    `stop_loss_type` VARCHAR(16) NOT NULL   DEFAULT 'MARKET',
    `take_profit_type` VARCHAR(16) NOT NULL DEFAULT 'MARKET',
    `margin` DOUBLE,
    `duplicate` BOOLEAN DEFAULT FALSE,
    `minimum_volume` DOUBLE,
    `others` VARCHAR(64),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`bot_id`),
    KEY (`api_id`),
    KEY (`pair_id`),
    KEY (`is_del`),
    CHECK(quantity >= 50),
    CHECK(leverage > 0),
    CHECK(margin > 0),
    CHECK(minimum_volume > 0),
    CHECK(take_profit > 0),
    CHECK(stop_loss > 0 AND stop_loss < 1),
    FOREIGN KEY(bot_id) REFERENCES bot_order(id),
    FOREIGN KEY(api_id) REFERENCES api(id),
    FOREIGN KEY(pair_id) REFERENCES pair(id)
) CHARACTER SET utf8;

ALTER TABLE `bot_order` ADD CONSTRAINT FOREIGN KEY(`config_id`) REFERENCES `bot_config`(id) ON DELETE CASCADE;

-- hyperopt
CREATE TABLE IF NOT EXISTS `hyperopt` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `start_at` DATETIME(6) NOT NULL,
    `end_at` DATETIME(6) NOT NULL,
    `channel` VARCHAR(32) NOT NULL,
    `params` VARCHAR(4096) NOT NULL,
    `days` INT NOT NULL,
    `loss` VARCHAR(32) NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    KEY (`channel`),
    KEY (`end_at`),
    KEY (`start_at`),
    KEY (`is_del`),
    KEY (`loss`)
) CHARACTER SET utf8;

-- performance
CREATE TABLE IF NOT EXISTS `performance` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `channel` VARCHAR(32) NOT NULL,
    `start_at` DATETIME(6) NOT NULL,
    `end_at` DATETIME(6) NOT NULL,
    `result` LONGTEXT NOT NULL,
    `hyperopt_id` INT NOT NULL,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    FOREIGN KEY(hyperopt_id) REFERENCES hyperopt(id),
    KEY (`channel`),
    KEY (`created_at`),
    KEY (`start_at`),
    KEY (`end_at`),
    KEY (`is_del`),
) CHARACTER SET utf8;

-- message
CREATE TABLE IF NOT EXISTS `message` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `message_timestamp` DATETIME(6),
    `recieve_timestamp` DATETIME(6),
    `channel` VARCHAR(32) NOT NULL,
    `content` VARCHAR(1024) NOT NULL,
    `symbol` VARCHAR(16),
    `action` VARCHAR(16),
    `quantity` DOUBLE,
    `entry` DOUBLE,
    `stop_loss` DOUBLE,
    `take_profit` DOUBLE,
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    CHECK(entry > 0),
    CHECK(stop_loss > 0),
    CHECK(take_profit > 0),
    KEY (`created_at`),
    KEY (`channel`),
    KEY (`symbol`),
    KEY (`action`),
    KEY (`is_del`)
) CHARACTER SET utf8;

-- trade history
CREATE TABLE IF NOT EXISTS `trade_history` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `bot_id` INT NOT NULL,
    `message_id` INT NOT NULL,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `status` VARCHAR(16) NOT NULL,
    `error` VARCHAR(1024),
    `open_order` VARCHAR(50),
    `sl_order` VARCHAR(50),
    `tp_order` VARCHAR(50),
    `is_del` BOOLEAN NOT NULL DEFAULT False,
    `quantity` DOUBLE,
    `balance` DOUBLE,
    KEY (`bot_id`),
    KEY (`message_id`),
    KEY (`created_at`),
    KEY (`status`),
    KEY (`is_del`),
    FOREIGN KEY(bot_id) REFERENCES bot_order(id),
    FOREIGN KEY(message_id) REFERENCES message(id)
) CHARACTER SET utf8;
