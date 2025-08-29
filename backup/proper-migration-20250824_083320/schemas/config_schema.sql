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
-- Name: popular_symbols; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.popular_symbols (
    id integer NOT NULL,
    symbol character varying(20) NOT NULL,
    description character varying(255),
    category character varying(50) DEFAULT 'stock'::character varying,
    priority integer DEFAULT 0,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.popular_symbols OWNER TO trading_user;

--
-- Name: popular_symbols_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.popular_symbols_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.popular_symbols_id_seq OWNER TO trading_user;

--
-- Name: popular_symbols_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.popular_symbols_id_seq OWNED BY public.popular_symbols.id;


--
-- Name: report_jobs; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.report_jobs (
    job_id character varying(100) NOT NULL,
    symbol character varying(20) NOT NULL,
    current_price numeric(10,2) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    include_news boolean DEFAULT true,
    include_technical boolean DEFAULT true,
    include_sentiment boolean DEFAULT true,
    user_email character varying(255),
    result jsonb,
    error text,
    notification_sent boolean DEFAULT false
);


ALTER TABLE public.report_jobs OWNER TO trading_user;

--
-- Name: risk_metrics; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.risk_metrics (
    id integer NOT NULL,
    date date NOT NULL,
    portfolio_value double precision NOT NULL,
    total_pnl double precision NOT NULL,
    daily_pnl double precision NOT NULL,
    max_drawdown double precision NOT NULL,
    sharpe_ratio double precision,
    var_95 double precision,
    volatility double precision,
    beta double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.risk_metrics OWNER TO trading_user;

--
-- Name: risk_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.risk_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.risk_metrics_id_seq OWNER TO trading_user;

--
-- Name: risk_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.risk_metrics_id_seq OWNED BY public.risk_metrics.id;


--
-- Name: trading_config; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.trading_config (
    id integer NOT NULL,
    key character varying(50) NOT NULL,
    value text NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.trading_config OWNER TO trading_user;

--
-- Name: trading_config_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.trading_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trading_config_id_seq OWNER TO trading_user;

--
-- Name: trading_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.trading_config_id_seq OWNED BY public.trading_config.id;


--
-- Name: popular_symbols id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.popular_symbols ALTER COLUMN id SET DEFAULT nextval('public.popular_symbols_id_seq'::regclass);


--
-- Name: risk_metrics id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.risk_metrics ALTER COLUMN id SET DEFAULT nextval('public.risk_metrics_id_seq'::regclass);


--
-- Name: trading_config id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_config ALTER COLUMN id SET DEFAULT nextval('public.trading_config_id_seq'::regclass);


--
-- Name: popular_symbols popular_symbols_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.popular_symbols
    ADD CONSTRAINT popular_symbols_pkey PRIMARY KEY (id);


--
-- Name: popular_symbols popular_symbols_symbol_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.popular_symbols
    ADD CONSTRAINT popular_symbols_symbol_key UNIQUE (symbol);


--
-- Name: report_jobs report_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.report_jobs
    ADD CONSTRAINT report_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: risk_metrics risk_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.risk_metrics
    ADD CONSTRAINT risk_metrics_pkey PRIMARY KEY (id);


--
-- Name: trading_config trading_config_key_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_config
    ADD CONSTRAINT trading_config_key_key UNIQUE (key);


--
-- Name: trading_config trading_config_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_config
    ADD CONSTRAINT trading_config_pkey PRIMARY KEY (id);


--
-- Name: idx_risk_metrics_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_risk_metrics_date ON public.risk_metrics USING btree (date);


--
-- PostgreSQL database dump complete
--

