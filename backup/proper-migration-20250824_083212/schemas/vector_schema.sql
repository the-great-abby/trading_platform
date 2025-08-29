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
-- Name: historical_news; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.historical_news (
    id integer NOT NULL,
    title text NOT NULL,
    content text,
    summary text,
    source character varying(100) NOT NULL,
    url text,
    author character varying(200),
    published_at timestamp without time zone NOT NULL,
    fetched_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sentiment_score double precision,
    impact_score double precision,
    confidence_score double precision,
    event_type character varying(50),
    affected_symbols jsonb,
    news_metadata jsonb,
    provider_id character varying(100),
    ticker character varying(10)
);


ALTER TABLE public.historical_news OWNER TO trading_user;

--
-- Name: historical_news_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.historical_news_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.historical_news_id_seq OWNER TO trading_user;

--
-- Name: historical_news_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.historical_news_id_seq OWNED BY public.historical_news.id;


--
-- Name: news_articles; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.news_articles (
    id integer NOT NULL,
    title text NOT NULL,
    content text,
    summary text,
    source character varying(100) NOT NULL,
    url text,
    author character varying(200),
    published_at timestamp without time zone NOT NULL,
    fetched_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sentiment_score double precision,
    impact_score double precision,
    confidence_score double precision,
    event_type character varying(50),
    affected_symbols jsonb,
    news_metadata jsonb,
    provider_id character varying(100),
    ticker character varying(10),
    vectorized boolean DEFAULT false,
    vector_embedding jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    vectorized_at timestamp without time zone
);


ALTER TABLE public.news_articles OWNER TO trading_user;

--
-- Name: news_articles_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.news_articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.news_articles_id_seq OWNER TO trading_user;

--
-- Name: news_articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.news_articles_id_seq OWNED BY public.news_articles.id;


--
-- Name: news_cache; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.news_cache (
    symbol character varying(10) NOT NULL,
    source character varying(100) NOT NULL,
    earliest_date timestamp without time zone,
    latest_date timestamp without time zone,
    total_articles integer DEFAULT 0,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.news_cache OWNER TO trading_user;

--
-- Name: news_historical; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.news_historical (
    id integer NOT NULL,
    title text NOT NULL,
    content text,
    summary text,
    source character varying(100) NOT NULL,
    url text,
    author character varying(200),
    published_at timestamp without time zone NOT NULL,
    fetched_at timestamp without time zone,
    sentiment_score double precision,
    impact_score double precision,
    confidence_score double precision,
    event_type character varying(50),
    affected_symbols json,
    news_metadata json,
    provider_id character varying(100),
    ticker character varying(10)
);


ALTER TABLE public.news_historical OWNER TO trading_user;

--
-- Name: news_historical_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.news_historical_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.news_historical_id_seq OWNER TO trading_user;

--
-- Name: news_historical_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.news_historical_id_seq OWNED BY public.news_historical.id;


--
-- Name: vector_embeddings; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.vector_embeddings (
    id character varying(100) NOT NULL,
    content text NOT NULL,
    embedding public.vector(128),
    meta_info jsonb,
    vector_type character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vector_embeddings OWNER TO trading_user;

--
-- Name: vectorization_jobs; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.vectorization_jobs (
    job_id character varying(255) NOT NULL,
    data_type character varying(50) NOT NULL,
    symbol character varying(20),
    data jsonb NOT NULL,
    priority integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT now(),
    status character varying(20) DEFAULT 'pending'::character varying,
    progress double precision DEFAULT 0.0,
    message text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    retry_count integer DEFAULT 0,
    max_retries integer DEFAULT 3
);


ALTER TABLE public.vectorization_jobs OWNER TO trading_user;

--
-- Name: vectorization_logs; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.vectorization_logs (
    id integer NOT NULL,
    job_id character varying(255) NOT NULL,
    level character varying(20) NOT NULL,
    message text NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    metadata jsonb
);


ALTER TABLE public.vectorization_logs OWNER TO trading_user;

--
-- Name: vectorization_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.vectorization_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vectorization_logs_id_seq OWNER TO trading_user;

--
-- Name: vectorization_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.vectorization_logs_id_seq OWNED BY public.vectorization_logs.id;


--
-- Name: vectorization_metrics; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.vectorization_metrics (
    id integer NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_value double precision NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    metadata jsonb
);


ALTER TABLE public.vectorization_metrics OWNER TO trading_user;

--
-- Name: vectorization_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: trading_user
--

CREATE SEQUENCE public.vectorization_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.vectorization_metrics_id_seq OWNER TO trading_user;

--
-- Name: vectorization_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trading_user
--

ALTER SEQUENCE public.vectorization_metrics_id_seq OWNED BY public.vectorization_metrics.id;


--
-- Name: historical_news id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.historical_news ALTER COLUMN id SET DEFAULT nextval('public.historical_news_id_seq'::regclass);


--
-- Name: news_articles id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.news_articles ALTER COLUMN id SET DEFAULT nextval('public.news_articles_id_seq'::regclass);


--
-- Name: news_historical id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.news_historical ALTER COLUMN id SET DEFAULT nextval('public.news_historical_id_seq'::regclass);


--
-- Name: vectorization_logs id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_logs ALTER COLUMN id SET DEFAULT nextval('public.vectorization_logs_id_seq'::regclass);


--
-- Name: vectorization_metrics id; Type: DEFAULT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_metrics ALTER COLUMN id SET DEFAULT nextval('public.vectorization_metrics_id_seq'::regclass);


--
-- Name: historical_news historical_news_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.historical_news
    ADD CONSTRAINT historical_news_pkey PRIMARY KEY (id);


--
-- Name: news_articles news_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_pkey PRIMARY KEY (id);


--
-- Name: news_cache news_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.news_cache
    ADD CONSTRAINT news_cache_pkey PRIMARY KEY (symbol, source);


--
-- Name: news_historical news_historical_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.news_historical
    ADD CONSTRAINT news_historical_pkey PRIMARY KEY (id);


--
-- Name: vector_embeddings vector_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vector_embeddings
    ADD CONSTRAINT vector_embeddings_pkey PRIMARY KEY (id);


--
-- Name: vectorization_jobs vectorization_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_jobs
    ADD CONSTRAINT vectorization_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: vectorization_logs vectorization_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_logs
    ADD CONSTRAINT vectorization_logs_pkey PRIMARY KEY (id);


--
-- Name: vectorization_metrics vectorization_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_metrics
    ADD CONSTRAINT vectorization_metrics_pkey PRIMARY KEY (id);


--
-- Name: idx_cache_source; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_cache_source ON public.news_cache USING btree (source);


--
-- Name: idx_meta_info; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_meta_info ON public.vector_embeddings USING gin (meta_info);


--
-- Name: idx_news_articles_event_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_event_type ON public.news_articles USING btree (event_type);


--
-- Name: idx_news_articles_impact; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_impact ON public.news_articles USING btree (impact_score);


--
-- Name: idx_news_articles_published_at; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_published_at ON public.news_articles USING btree (published_at);


--
-- Name: idx_news_articles_sentiment; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_sentiment ON public.news_articles USING btree (sentiment_score);


--
-- Name: idx_news_articles_source; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_source ON public.news_articles USING btree (source);


--
-- Name: idx_news_articles_ticker; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_ticker ON public.news_articles USING btree (ticker);


--
-- Name: idx_news_articles_vectorized; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_articles_vectorized ON public.news_articles USING btree (vectorized);


--
-- Name: idx_news_event_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_event_type ON public.historical_news USING btree (event_type);


--
-- Name: idx_news_impact; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_impact ON public.historical_news USING btree (impact_score);


--
-- Name: idx_news_published_at; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_published_at ON public.historical_news USING btree (published_at);


--
-- Name: idx_news_sentiment; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_sentiment ON public.historical_news USING btree (sentiment_score);


--
-- Name: idx_news_source; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_source ON public.historical_news USING btree (source);


--
-- Name: idx_news_ticker; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_news_ticker ON public.historical_news USING btree (ticker);


--
-- Name: idx_vector_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vector_type ON public.vector_embeddings USING btree (vector_type);


--
-- Name: idx_vectorization_jobs_created_at; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_jobs_created_at ON public.vectorization_jobs USING btree (created_at);


--
-- Name: idx_vectorization_jobs_data_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_jobs_data_type ON public.vectorization_jobs USING btree (data_type);


--
-- Name: idx_vectorization_jobs_status; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_jobs_status ON public.vectorization_jobs USING btree (status);


--
-- Name: idx_vectorization_jobs_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_jobs_symbol ON public.vectorization_jobs USING btree (symbol);


--
-- Name: idx_vectorization_logs_job_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_logs_job_id ON public.vectorization_logs USING btree (job_id);


--
-- Name: idx_vectorization_logs_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_logs_timestamp ON public.vectorization_logs USING btree ("timestamp");


--
-- Name: idx_vectorization_metrics_name_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_vectorization_metrics_name_timestamp ON public.vectorization_metrics USING btree (metric_name, "timestamp");


--
-- Name: vectorization_logs vectorization_logs_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.vectorization_logs
    ADD CONSTRAINT vectorization_logs_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.vectorization_jobs(job_id);


--
-- PostgreSQL database dump complete
--

