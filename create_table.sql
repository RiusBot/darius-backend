-- permission
CREATE TABLE `permission` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `role_id` int(11),
    `service` varchar(50) UNIQUE NOT NULL,
    KEY (`role_id`)
) CHARACTER SET utf8;

-- role
CREATE TABLE `role` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `permission_id` int(11) NOT NULL,
    `name` varchar(50) NOT NULL,
    KEY (`permission_id`),
    KEY (`name`),
    CONSTRAINT FOREIGN KEY(`permission_id`) REFERENCES `permission`(id) ON DELETE CASCADE
) CHARACTER SET utf8;


ALTER TABLE `permission` ADD  CONSTRAINT FOREIGN KEY(`role_id`) REFERENCES `role`(id) ON DELETE CASCADE;


-- user
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
  `user_name` varchar(50) NOT NULL,
  `email` varchar(50) UNIQUE NOT NULL,
  `password` varchar(50),
  `role_id` int(11) NOT NULL,
   KEY (`user_name`),
   KEY (`email`),
   KEY (`created_at`),
   CONSTRAINT FOREIGN KEY (`role_id`) REFERENCES `role`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- plan
CREATE TABLE `plan` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `price` decimal(19, 4) NOT NULL,
  `day` decimal(10, 0) NOT NULL -- should modify the term, available_day
  `name` varchar(50) UNIQUE NOT NULL,
  `channel` varchar(50) NOT NULL,
  KEY (`name`),
  KEY (`created_at`),
  KEY (`channel`),
  CHECK(day >= 0),
  CHECK(price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- subscription
CREATE TABLE `subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `user_id` int(11) NOT NULL,
  `expire_date` datetime,
  `plan_id` int(11) NOT NULL,
  `status` varchar(16) NOT NULL,
  KEY (`user_id`),
  KEY (`expire_date`),
  KEY (`plan_id`),
  KEY (`status`),
  CONSTRAINT FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  CONSTRAINT FOREIGN KEY (`plan_id`) REFERENCES `plan`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- api
CREATE TABLE `api` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` int(11) NOT NULL,
    `api_key` varchar(50) UNIQUE NOT NULL,
    `api_secret` varchar(50) UNIQUE NOT NULL,
    `exchange` varchar(16) NOT NULL,
    KEY (`user_id`),
    KEY (`exchange`),
    CONSTRAINT FOREIGN KEY(`user_id`) REFERENCES `user`(id)
) CHARACTER SET utf8;

-- bot order
CREATE TABLE IF NOT EXISTS `bot_order` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `channel` VARCHAR(32) NOT NULL,
    `status` VARCHAR(16) NOT NULL,
    `config_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    KEY (`user_id`),
    KEY (`status`),
    KEY (`channel`),
    KEY (`created_at`),
    KEY (`config_id`),
    FOREIGN KEY(user_id) REFERENCES user(id)
) CHARACTER SET utf8;


-- bot config
CREATE TABLE IF NOT EXISTS `bot_config` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `bot_id` INT,
    `api_id` INT NOT NULL,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `test` BOOLEAN  DEFAULT FALSE,
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
    KEY (`bot_id`),
    CHECK(quantity >= 50),
    CHECK(leverage > 0),
    CHECK(margin > 0),
    CHECK(minimum_volume > 0),
    CHECK(take_profit > 0),
    CHECK(stop_loss > 0 AND stop_loss < 1),
    FOREIGN KEY(bot_id) REFERENCES bot_order(id),
    FOREIGN KEY(api_id) REFERENCES api(id)
) CHARACTER SET utf8;

ALTER TABLE `bot_order` ADD CONSTRAINT FOREIGN KEY(`config_id`) REFERENCES `bot_config`(id) ON DELETE CASCADE;

-- message
CREATE TABLE IF NOT EXISTS `message` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `message_timestamp` DATETIME(6),
    `recieve_timestamp` DATETIME(6),
    `channel` VARCHAR(32) NOT NULL,
    `content` VARCHAR(1024) NOT NULL,
    `symbol` VARCHAR(16),
    `action` VARCHAR(16),
    `entry` DOUBLE,
    `stop_loss` DOUBLE,
    `take_profit` DOUBLE,
    CHECK(entry > 0),
    CHECK(stop_loss > 0),
    CHECK(take_profit > 0),
    KEY (`created_at`),
    KEY (`channel`),
    KEY (`symbol`),
    KEY (`action`)
) CHARACTER SET utf8;

-- trade history
CREATE TABLE IF NOT EXISTS `trade_history` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `bot_id` INT NOT NULL,
    `message_id` INT NOT NULL,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `status` VARCHAR(16) NOT NULL,
    `error` VARCHAR(1024),
    `open_order` VARCHAR(50),
    `sl_order` VARCHAR(50),
    `tp_order` VARCHAR(50),
    KEY (`bot_id`),
    KEY (`message_id`),
    KEY (`created_at`),
    KEY (`status`),
    FOREIGN KEY(bot_id) REFERENCES bot_order(id),
    FOREIGN KEY(message_id) REFERENCES message(id)
) CHARACTER SET utf8;

ALTER TABLE role add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE permission add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE subscription add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE plan add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE user add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE api add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE bot_order add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE bot_config add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE trade_history add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
ALTER TABLE message add COLUMN is_del BOOLEAN NOT NULL DEFAULT False;
