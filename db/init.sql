-- 文字化けを防ぐ設定(日本語)
SET NAMES utf8mb4;

CREATE TABLE `クラス` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `クラス名` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `講師` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `苗字` VARCHAR(100) NOT NULL,
    `名前` VARCHAR(100) NOT NULL,
    `ログイン_id` VARCHAR(100) UNIQUE NOT NULL,
    `パスワード` VARCHAR(255) NOT NULL,
    `電話番号` VARCHAR(20) UNIQUE,
    `メール` VARCHAR(255) UNIQUE,
    `生年月日` DATE,
    `担当クラス_id`INT,
    FOREIGN KEY (`担当クラス_id`) REFERENCES `クラス`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `保護者` (
    `id` INT AUTO_INCREMENT PRIMARY KEY, 
    `苗字` VARCHAR(100) NOT NULL,
    `名前` VARCHAR(100) NOT NULL,
    `電話番号` VARCHAR(20) UNIQUE NOT NULL,
    `メール` VARCHAR(100) UNIQUE NOT NULL,
    `生年月日` DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `学生`(
    `id` INT AUTO_INCREMENT PRIMARY KEY, 
    `苗字` VARCHAR(100) NOT NULL,
    `名前` VARCHAR(100) NOT NULL,
    `電話番号` VARCHAR(20) UNIQUE NOT NULL,
    `メール` VARCHAR(255) UNIQUE NOT NULL,
    `生年月日` DATE NOT NULL,
    `クラス_id` INT,
    `保護者_id` INT,
    FOREIGN KEY (`クラス_id`) REFERENCES `クラス`(`id`)
    FOREIGN KEY (`保護者_id`) REFERENCES `保護者`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `成績表`(
    `id` INT AUTO_INCREMENT PRIMARY KEY, 
    `学生_id` INT,
    `受験者数` INT,
    `コメント` TEXT,
    `推薦大学` JSON,
    `実施日` DATE,
    `統合順位` INT,
    `クラス順位` INT,
    `s3_file_url` VARCHAR(255),
    `確認ステータス` VARCHAR(50) DEFAULT '未確認',
    FOREIGN KEY (`学生_id`) REFERENCES `学生`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `科目`(
    `id` INT AUTO_INCREMENT PRIMARY KEY, 
    `科目名` VARCHAR(100) NOT NULL,
    `科目区分` VARCHAR (50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `成績詳細`(
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `点数` INT、
    `偏差値` DECIMAL(5,2)、
    `順位` INT 
    `科目_id` INT,
    `成績表_id` INT,
    FOREIGN KEY (`科目_id`) REFERENCES `科目`(`id`)
    FOREIGN KEY (`成績表_id`) REFERENCES `成績表`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `送信履歴`(
    `id` INT AUTO_INCREMENT PRIMARY KEY, 
    `講師_id` INT,
    `保護者_id` INT,
    `成績表_id` INT,
    `送信日時` DATETIME NOT NULL,
    `送信ステータス` VARCHAR(50) NOT NULL,
    `送信チャネル` JSON,
    `送信内容` TEXT,
    FOREIGN KEY (`講師_id`) REFERENCES `講師`(`id`)
    FOREIGN KEY (`保護者_id`) REFERENCES `保護者`(`id`)
    FOREIGN KEY (`成績表_id`) REFERENCES `成績表`(`id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--　科目の初期データ
INSERT INTO `科目` (`科目名`) VALUES 
(`国語`), (`数学`), (`英語`), (`歴史`), (`生命工学`), 
(`地球科学`), (`物理`), (`科学`); 
