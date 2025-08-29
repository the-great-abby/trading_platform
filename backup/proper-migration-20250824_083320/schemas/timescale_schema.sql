--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: historical_prices; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.historical_prices (
    symbol character varying(10) NOT NULL,
    date date NOT NULL,
    open_price numeric(10,4) NOT NULL,
    high_price numeric(10,4) NOT NULL,
    low_price numeric(10,4) NOT NULL,
    close_price numeric(10,4) NOT NULL,
    volume integer NOT NULL,
    provider character varying(50) NOT NULL,
    "interval" character varying(10) DEFAULT '1d'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.historical_prices OWNER TO trading_user;

--
-- Name: backtest_equity_curves; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.backtest_equity_curves (
    id integer NOT NULL,
    run_id character varying(50) NOT NULL,
    date date NOT NULL,
    portfolio_value double precision NOT NULL,
    cash double precision DEFAULT 0.0 NOT NULL,
    positions_value double precision DEFAULT 0.0 NOT NULL,
    total_pnl double precision DEFAULT 0.0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backtest_equity_curves OWNER TO trading_user;

--
-- Name: backtest_equity_curves_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.backtest_equity_curves_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backtest_equity_curves_id_seq OWNER TO trading_user;

--
-- Name: backtest_equity_curves_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.backtest_equity_curves_id_seq OWNED BY public.backtest_equity_curves.id;


--
-- Name: backtest_runs; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.backtest_runs (
    id integer NOT NULL,
    run_id character varying(50) NOT NULL,
    strategy_name character varying(100) NOT NULL,
    backtest_name character varying(200),
    symbols text NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    initial_capital double precision NOT NULL,
    final_capital double precision NOT NULL,
    total_return double precision NOT NULL,
    total_return_pct double precision NOT NULL,
    max_drawdown_pct double precision NOT NULL,
    sharpe_ratio double precision NOT NULL,
    total_trades integer NOT NULL,
    winning_trades integer NOT NULL,
    losing_trades integer NOT NULL,
    win_rate double precision NOT NULL,
    profit_factor double precision NOT NULL,
    avg_win double precision NOT NULL,
    avg_loss double precision NOT NULL,
    database_only character varying(5) DEFAULT 'false'::character varying NOT NULL,
    data_provider character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone
);


ALTER TABLE public.backtest_runs OWNER TO trading_user;

--
-- Name: backtest_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.backtest_runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backtest_runs_id_seq OWNER TO trading_user;

--
-- Name: backtest_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.backtest_runs_id_seq OWNED BY public.backtest_runs.id;


--
-- Name: backtest_trades; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.backtest_trades (
    id integer NOT NULL,
    run_id character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    symbol character varying(10) NOT NULL,
    action character varying(10) NOT NULL,
    quantity integer NOT NULL,
    price double precision NOT NULL,
    value double precision NOT NULL,
    pnl double precision DEFAULT 0.0 NOT NULL,
    confidence double precision DEFAULT 0.5 NOT NULL,
    portfolio_value double precision DEFAULT 0.0 NOT NULL,
    cash double precision DEFAULT 0.0 NOT NULL,
    position_value double precision DEFAULT 0.0 NOT NULL,
    total_pnl double precision DEFAULT 0.0 NOT NULL,
    trade_pnl double precision DEFAULT 0.0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.backtest_trades OWNER TO trading_user;

--
-- Name: backtest_trades_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.backtest_trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.backtest_trades_id_seq OWNER TO trading_user;

--
-- Name: backtest_trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.backtest_trades_id_seq OWNED BY public.backtest_trades.id;


--
-- Name: earnings_reports; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.earnings_reports (
    id integer NOT NULL,
    symbol character varying(10) NOT NULL,
    quarter character varying(10) NOT NULL,
    year integer NOT NULL,
    eps numeric(10,4),
    revenue numeric(20,2),
    report_date date NOT NULL,
    eps_estimate numeric(10,4),
    revenue_estimate numeric(20,2),
    eps_surprise numeric(10,4),
    revenue_surprise numeric(20,2),
    guidance text,
    conference_call_date date,
    notes text,
    vectorized boolean DEFAULT false,
    vector_embedding jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    vectorized_at timestamp without time zone,
    source character varying(50) DEFAULT 'unknown'::character varying,
    raw_data jsonb
);


ALTER TABLE public.earnings_reports OWNER TO trading_user;

--
-- Name: earnings_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.earnings_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.earnings_reports_id_seq OWNER TO trading_user;

--
-- Name: earnings_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.earnings_reports_id_seq OWNED BY public.earnings_reports.id;


--
-- Name: historical_options_snapshots; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.historical_options_snapshots (
    id integer NOT NULL,
    symbol character varying,
    snapshot_date date,
    expiration character varying,
    strike double precision,
    option_type character varying,
    price double precision,
    volume integer,
    open_interest integer,
    delta double precision,
    gamma double precision,
    theta double precision,
    vega double precision,
    implied_volatility double precision,
    underlying_price double precision,
    data_source character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.historical_options_snapshots OWNER TO trading_user;

--
-- Name: historical_options_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.historical_options_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.historical_options_snapshots_id_seq OWNER TO trading_user;

--
-- Name: historical_options_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.historical_options_snapshots_id_seq OWNED BY public.historical_options_snapshots.id;


--
-- Name: market_data; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.market_data (
    id integer NOT NULL,
    symbol character varying(10) NOT NULL,
    date date NOT NULL,
    open_price numeric(10,4) NOT NULL,
    high_price numeric(10,4) NOT NULL,
    low_price numeric(10,4) NOT NULL,
    close_price numeric(10,4) NOT NULL,
    volume integer NOT NULL,
    provider character varying(50) NOT NULL,
    "interval" character varying(10) DEFAULT '1d'::character varying NOT NULL,
    vectorized boolean DEFAULT false,
    vector_embedding jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    vectorized_at timestamp without time zone
);


ALTER TABLE public.market_data OWNER TO trading_user;

--
-- Name: market_data_cache; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.market_data_cache (
    symbol character varying(10) NOT NULL,
    provider character varying(50) NOT NULL,
    "interval" character varying(10) DEFAULT '1d'::character varying NOT NULL,
    earliest_date date,
    latest_date date,
    total_records integer DEFAULT 0,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.market_data_cache OWNER TO trading_user;

--
-- Name: market_data_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.market_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.market_data_id_seq OWNER TO trading_user;

--
-- Name: market_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.market_data_id_seq OWNED BY public.market_data.id;


--
-- Name: options_contracts_cache; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.options_contracts_cache (
    id integer NOT NULL,
    symbol character varying,
    expiration character varying,
    strike double precision,
    option_type character varying,
    price double precision,
    volume integer,
    open_interest integer,
    delta double precision,
    gamma double precision,
    theta double precision,
    vega double precision,
    implied_volatility double precision,
    cache_date date,
    last_updated timestamp without time zone
);


ALTER TABLE public.options_contracts_cache OWNER TO trading_user;

--
-- Name: options_contracts_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.options_contracts_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.options_contracts_cache_id_seq OWNER TO trading_user;

--
-- Name: options_contracts_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.options_contracts_cache_id_seq OWNED BY public.options_contracts_cache.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    order_id character varying(50) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    symbol character varying(10) NOT NULL,
    action character varying(10) NOT NULL,
    quantity integer NOT NULL,
    price double precision NOT NULL,
    order_type character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    strategy character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.orders OWNER TO trading_user;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.orders_id_seq OWNER TO trading_user;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: positions; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.positions (
    id integer NOT NULL,
    symbol character varying(10) NOT NULL,
    quantity integer NOT NULL,
    entry_price double precision NOT NULL,
    current_price double precision NOT NULL,
    pnl double precision,
    strategy character varying(50) NOT NULL,
    "timestamp" timestamp without time zone,
    is_active boolean
);


ALTER TABLE public.positions OWNER TO trading_user;

--
-- Name: positions_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.positions_id_seq OWNER TO trading_user;

--
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.positions_id_seq OWNED BY public.positions.id;


--
-- Name: signals; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.signals (
    id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    symbol character varying(10) NOT NULL,
    signal_type character varying(20) NOT NULL,
    direction character varying(10) NOT NULL,
    strength double precision,
    strategy character varying(100),
    confidence double precision,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.signals OWNER TO trading_user;

--
-- Name: signals_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.signals_id_seq OWNER TO trading_user;

--
-- Name: signals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.signals_id_seq OWNED BY public.signals.id;


--
-- Name: trades; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.trades (
    id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    symbol character varying(10) NOT NULL,
    action character varying(10) NOT NULL,
    quantity integer NOT NULL,
    price double precision NOT NULL,
    value double precision NOT NULL,
    strategy character varying(100),
    confidence double precision,
    pnl double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.trades OWNER TO trading_user;

--
-- Name: trades_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trades_id_seq OWNER TO trading_user;

--
-- Name: trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.trades_id_seq OWNED BY public.trades.id;


--
-- Name: backtest_equity_curves id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_equity_curves ALTER COLUMN id SET DEFAULT nextval('public.backtest_equity_curves_id_seq'::regclass);


--
-- Name: backtest_runs id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_runs ALTER COLUMN id SET DEFAULT nextval('public.backtest_runs_id_seq'::regclass);


--
-- Name: backtest_trades id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_trades ALTER COLUMN id SET DEFAULT nextval('public.backtest_trades_id_seq'::regclass);


--
-- Name: earnings_reports id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.earnings_reports ALTER COLUMN id SET DEFAULT nextval('public.earnings_reports_id_seq'::regclass);


--
-- Name: historical_options_snapshots id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.historical_options_snapshots ALTER COLUMN id SET DEFAULT nextval('public.historical_options_snapshots_id_seq'::regclass);


--
-- Name: market_data id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.market_data ALTER COLUMN id SET DEFAULT nextval('public.market_data_id_seq'::regclass);


--
-- Name: options_contracts_cache id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.options_contracts_cache ALTER COLUMN id SET DEFAULT nextval('public.options_contracts_cache_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: positions id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.positions ALTER COLUMN id SET DEFAULT nextval('public.positions_id_seq'::regclass);


--
-- Name: signals id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.signals ALTER COLUMN id SET DEFAULT nextval('public.signals_id_seq'::regclass);


--
-- Name: trades id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trades ALTER COLUMN id SET DEFAULT nextval('public.trades_id_seq'::regclass);


--
-- Name: backtest_equity_curves backtest_equity_curves_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_equity_curves
    ADD CONSTRAINT backtest_equity_curves_pkey PRIMARY KEY (id);


--
-- Name: backtest_runs backtest_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_runs
    ADD CONSTRAINT backtest_runs_pkey PRIMARY KEY (id);


--
-- Name: backtest_runs backtest_runs_run_id_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_runs
    ADD CONSTRAINT backtest_runs_run_id_key UNIQUE (run_id);


--
-- Name: backtest_trades backtest_trades_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.backtest_trades
    ADD CONSTRAINT backtest_trades_pkey PRIMARY KEY (id);


--
-- Name: earnings_reports earnings_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.earnings_reports
    ADD CONSTRAINT earnings_reports_pkey PRIMARY KEY (id);


--
-- Name: historical_options_snapshots historical_options_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.historical_options_snapshots
    ADD CONSTRAINT historical_options_snapshots_pkey PRIMARY KEY (id);


--
-- Name: historical_prices historical_prices_symbol_date_unique; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.historical_prices
    ADD CONSTRAINT historical_prices_symbol_date_unique UNIQUE (symbol, date);


--
-- Name: market_data_cache market_data_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.market_data_cache
    ADD CONSTRAINT market_data_cache_pkey PRIMARY KEY (symbol, provider, "interval");


--
-- Name: market_data market_data_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_pkey PRIMARY KEY (id);


--
-- Name: market_data market_data_symbol_date_provider_interval_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_symbol_date_provider_interval_key UNIQUE (symbol, date, provider, "interval");


--
-- Name: options_contracts_cache options_contracts_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.options_contracts_cache
    ADD CONSTRAINT options_contracts_cache_pkey PRIMARY KEY (id);


--
-- Name: orders orders_order_id_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_order_id_key UNIQUE (order_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (id);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (id);


--
-- Name: historical_prices_date_idx; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX historical_prices_date_idx ON public.historical_prices USING btree (date DESC);


--
-- Name: idx_action; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_action ON public.backtest_trades USING btree (action);


--
-- Name: idx_backtest_name; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_backtest_name ON public.backtest_runs USING btree (backtest_name);


--
-- Name: idx_cache_provider; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_cache_provider ON public.market_data_cache USING btree (provider);


--
-- Name: idx_cache_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_cache_symbol ON public.market_data_cache USING btree (symbol);


--
-- Name: idx_created_at; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_created_at ON public.backtest_runs USING btree (created_at);


--
-- Name: idx_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_date ON public.backtest_equity_curves USING btree (date);


--
-- Name: idx_date_range; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_date_range ON public.backtest_runs USING btree (start_date, end_date);


--
-- Name: idx_earnings_reports_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_date ON public.earnings_reports USING btree (report_date);


--
-- Name: idx_earnings_reports_quarter_year; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_quarter_year ON public.earnings_reports USING btree (quarter, year);


--
-- Name: idx_earnings_reports_source; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_source ON public.earnings_reports USING btree (source);


--
-- Name: idx_earnings_reports_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_symbol ON public.earnings_reports USING btree (symbol);


--
-- Name: idx_earnings_reports_symbol_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_symbol_date ON public.earnings_reports USING btree (symbol, report_date);


--
-- Name: idx_earnings_reports_vectorized; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_earnings_reports_vectorized ON public.earnings_reports USING btree (vectorized);


--
-- Name: idx_market_data_interval; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_market_data_interval ON public.market_data USING btree ("interval");


--
-- Name: idx_market_data_provider; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_market_data_provider ON public.market_data USING btree (provider);


--
-- Name: idx_market_data_symbol_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_market_data_symbol_date ON public.market_data USING btree (symbol, date);


--
-- Name: idx_market_data_vectorized; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_market_data_vectorized ON public.market_data USING btree (vectorized);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_orders_status ON public.orders USING btree (status);


--
-- Name: idx_orders_strategy; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_orders_strategy ON public.orders USING btree (strategy);


--
-- Name: idx_orders_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_orders_symbol ON public.orders USING btree (symbol);


--
-- Name: idx_orders_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_orders_timestamp ON public.orders USING btree ("timestamp");


--
-- Name: idx_provider_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_provider_symbol ON public.historical_prices USING btree (provider, symbol);


--
-- Name: idx_run_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_run_id ON public.backtest_runs USING btree (run_id);


--
-- Name: idx_signals_strategy; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_signals_strategy ON public.signals USING btree (strategy);


--
-- Name: idx_signals_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_signals_symbol ON public.signals USING btree (symbol);


--
-- Name: idx_signals_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_signals_timestamp ON public.signals USING btree ("timestamp");


--
-- Name: idx_signals_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_signals_type ON public.signals USING btree (signal_type);


--
-- Name: idx_strategy; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_strategy ON public.backtest_runs USING btree (strategy_name);


--
-- Name: idx_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_symbol ON public.backtest_trades USING btree (symbol);


--
-- Name: idx_symbol_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_symbol_date ON public.historical_prices USING btree (symbol, date);


--
-- Name: idx_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_timestamp ON public.backtest_trades USING btree ("timestamp");


--
-- Name: idx_trades_action; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trades_action ON public.trades USING btree (action);


--
-- Name: idx_trades_strategy; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trades_strategy ON public.trades USING btree (strategy);


--
-- Name: idx_trades_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trades_symbol ON public.trades USING btree (symbol);


--
-- Name: idx_trades_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trades_timestamp ON public.trades USING btree ("timestamp");


--
-- Name: ix_historical_options_snapshots_expiration; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_historical_options_snapshots_expiration ON public.historical_options_snapshots USING btree (expiration);


--
-- Name: ix_historical_options_snapshots_snapshot_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_historical_options_snapshots_snapshot_date ON public.historical_options_snapshots USING btree (snapshot_date);


--
-- Name: ix_historical_options_snapshots_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_historical_options_snapshots_symbol ON public.historical_options_snapshots USING btree (symbol);


--
-- Name: ix_options_contracts_cache_cache_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_options_contracts_cache_cache_date ON public.options_contracts_cache USING btree (cache_date);


--
-- Name: ix_options_contracts_cache_expiration; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_options_contracts_cache_expiration ON public.options_contracts_cache USING btree (expiration);


--
-- Name: ix_options_contracts_cache_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX ix_options_contracts_cache_symbol ON public.options_contracts_cache USING btree (symbol);


--
-- Name: historical_prices ts_insert_blocker; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.historical_prices FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();


--
-- PostgreSQL database dump complete
--

