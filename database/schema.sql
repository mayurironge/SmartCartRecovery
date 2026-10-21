-- Generated from backend/models. Keep in sync when models change.
CREATE TABLE customers (
	customer_id SERIAL NOT NULL,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	email VARCHAR(150) NOT NULL,
	phone VARCHAR(20) NOT NULL,
	PRIMARY KEY (customer_id),
	UNIQUE (email)
);

CREATE TABLE products (
	product_id SERIAL NOT NULL,
	product_name VARCHAR(150) NOT NULL,
	category VARCHAR(100) NOT NULL,
	price NUMERIC(10, 2) NOT NULL,
	stock INTEGER NOT NULL,
	PRIMARY KEY (product_id)
);

CREATE TABLE carts (
	cart_id SERIAL NOT NULL,
	customer_id INTEGER NOT NULL,
	status VARCHAR(20) NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (cart_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE cart_events (
	event_id SERIAL NOT NULL,
	cart_id INTEGER NOT NULL,
	event_type VARCHAR(50) NOT NULL,
	event_time TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (event_id),
	FOREIGN KEY(cart_id) REFERENCES carts (cart_id)
);

CREATE TABLE cart_items (
	cart_item_id SERIAL NOT NULL,
	cart_id INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	added_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (cart_item_id),
	FOREIGN KEY(cart_id) REFERENCES carts (cart_id),
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

CREATE TABLE cart_recovery (
	recovery_id SERIAL NOT NULL,
	cart_id INTEGER NOT NULL,
	recovery_status VARCHAR NOT NULL,
	attempts INTEGER DEFAULT '0' NOT NULL,
	detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
	notified_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (recovery_id),
	FOREIGN KEY(cart_id) REFERENCES carts (cart_id)
);

CREATE INDEX ix_cart_recovery_recovery_id ON cart_recovery (recovery_id);

CREATE UNIQUE INDEX uq_cart_recovery_open_cart ON cart_recovery (cart_id) WHERE recovery_status = 'PENDING';

CREATE TABLE orders (
	order_id SERIAL NOT NULL,
	customer_id INTEGER NOT NULL,
	cart_id INTEGER NOT NULL,
	total_amount NUMERIC(10, 2) NOT NULL,
	status VARCHAR(20) NOT NULL,
	order_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (order_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id),
	FOREIGN KEY(cart_id) REFERENCES carts (cart_id)
);

CREATE TABLE notifications (
	notification_id SERIAL NOT NULL,
	customer_id INTEGER,
	recovery_id INTEGER,
	channel VARCHAR,
	message TEXT,
	sent BOOLEAN,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (notification_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id),
	FOREIGN KEY(recovery_id) REFERENCES cart_recovery (recovery_id)
);

CREATE UNIQUE INDEX uq_notifications_recovery_id ON notifications (recovery_id);

CREATE TABLE order_items (
	order_item_id SERIAL NOT NULL,
	order_id INTEGER NOT NULL,
	product_id INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	price NUMERIC(10, 2) NOT NULL,
	PRIMARY KEY (order_item_id),
	FOREIGN KEY(order_id) REFERENCES orders (order_id),
	FOREIGN KEY(product_id) REFERENCES products (product_id)
);

