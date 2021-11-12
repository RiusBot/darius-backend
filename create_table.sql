-- permission
CREATE TABLE `permission` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `role_id` int(11) NOT NULL,
    `service` varchar(50) NOT NULL,
    KEY (`role_id`)
) CHARACTER SET utf8;

-- role
CREATE TABLE `role` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `permission_id` int(11) NOT NULL,
    KEY (`permission_id`),
    CONSTRAINT FOREIGN KEY(`permission_id`) REFERENCES `permission`(id)
) CHARACTER SET utf8;


ALTER TABLE `permission` ADD  CONSTRAINT FOREIGN KEY(`role_id`) REFERENCES `role`(id);


-- user
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_name` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `role_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
   KEY (`user_name`),
   KEY (`email`),
   KEY (`created_at`),
   CONSTRAINT FOREIGN KEY (`role_id`) REFERENCES `role`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- plan
CREATE TABLE `plan` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `price` decimal(19, 4) NOT NULL,
  `day` decimal(10, 0) NOT NULL -- should modify the term, available_day
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- subscription
CREATE TABLE `subscription` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` int(11) NOT NULL,
  `expire_date` datetime NOT NULL,
  `plan_id` int(11) NOT NULL,
  KEY (`user_id`),
  KEY (`expire_date`),
  KEY (`plan_id`),
  CONSTRAINT FOREIGN KEY (`user_id`) REFERENCES `user`(`id`),
  CONSTRAINT FOREIGN KEY (`plan_id`) REFERENCES `plan`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- api
CREATE TABLE `api` (
    `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id` int(11) NOT NULL,
        `api_key` varchar(50) NOT NULL,
    `api_secret` varchar(50) NOT NULL,
    KEY (`user_id`),
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
    FOREIGN KEY(config_id) REFERENCES bot_config(id),
    FOREIGN KEY(user_id) REFERENCES user(id)
) CHARACTER SET utf8;


-- bot config
CREATE TABLE IF NOT EXISTS `bot_config` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `bot_id` INT NOT NULL,
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
    FOREIGN KEY(bot_id) REFERENCES bot_order(id)
) CHARACTER SET utf8;

ALTER TABLE `bot_order` ADD CONSTRAINT FOREIGN KEY(`config_id`) REFERENCES `bot_config`(id);

-- message
CREATE TABLE IF NOT EXISTS `message` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6)   DEFAULT CURRENT_TIMESTAMP(6),
    `message_timestamp` DATETIME(6),
    `recieve_timestamp` DATETIME(6),
    `channel` VARCHAR(32) NOT NULL,
    `content` VARCHAR(1024) NOT NULL,
    `symbol` VARCHAR(16) NOT NULL,
    `action` VARCHAR(16),
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
    `error`  VARCHAR(1024) NOT NULL,
    KEY (`bot_id`),
    KEY (`message_id`),
    KEY (`created_at`),
    KEY (`status`),
    FOREIGN KEY(bot_id) REFERENCES bot_order(id),
    FOREIGN KEY(message_id) REFERENCES message(id)
) CHARACTER SET utf8;
