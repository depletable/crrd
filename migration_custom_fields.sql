-- migration_custom_fields.sql

ALTER TABLE users ADD COLUMN profile_picture TEXT;
ALTER TABLE users ADD COLUMN border_width TEXT;
ALTER TABLE users ADD COLUMN border_color TEXT;
ALTER TABLE users ADD COLUMN border_opacity REAL;
ALTER TABLE users ADD COLUMN card_bg_color TEXT;
ALTER TABLE users ADD COLUMN card_bg_image TEXT;
ALTER TABLE users ADD COLUMN card_bg_opacity REAL;
ALTER TABLE users ADD COLUMN page_bg_image TEXT;
ALTER TABLE users ADD COLUMN name_color TEXT;
ALTER TABLE users ADD COLUMN banner_image TEXT;
ALTER TABLE users ADD COLUMN show_banner INTEGER DEFAULT 1;
