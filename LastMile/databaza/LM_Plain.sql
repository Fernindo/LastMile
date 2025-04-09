--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

-- Started on 2025-03-28 11:53:40

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 258 (class 1255 OID 16592)
-- Name: log_audit(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_audit() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (tabulka, akcia, vykonal, novy_zaznam)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (tabulka, akcia, vykonal, povodny_zaznam, novy_zaznam)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (tabulka, akcia, vykonal, povodny_zaznam)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.log_audit() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 257 (class 1259 OID 16586)
-- Name: audit_log; Type: TABLE; Schema: public; Owner: admin_user
--

CREATE TABLE public.audit_log (
    tabulka text,
    akcia text,
    vykonal text,
    datum timestamp without time zone DEFAULT now(),
    povodny_zaznam jsonb,
    novy_zaznam jsonb
);


ALTER TABLE public.audit_log OWNER TO admin_user;

--
-- TOC entry 230 (class 1259 OID 16444)
-- Name: battery_packy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.battery_packy (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.battery_packy OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16443)
-- Name: battery_packy_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.battery_packy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.battery_packy_id_seq OWNER TO postgres;

--
-- TOC entry 5118 (class 0 OID 0)
-- Dependencies: 229
-- Name: battery_packy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.battery_packy_id_seq OWNED BY public.battery_packy.id;


--
-- TOC entry 234 (class 1259 OID 16462)
-- Name: datove_zasuvky; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.datove_zasuvky (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.datove_zasuvky OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16461)
-- Name: datove_zasuvky_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.datove_zasuvky_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.datove_zasuvky_id_seq OWNER TO postgres;

--
-- TOC entry 5121 (class 0 OID 0)
-- Dependencies: 233
-- Name: datove_zasuvky_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.datove_zasuvky_id_seq OWNED BY public.datove_zasuvky.id;


--
-- TOC entry 256 (class 1259 OID 16561)
-- Name: indikatory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.indikatory (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.indikatory OWNER TO postgres;

--
-- TOC entry 255 (class 1259 OID 16560)
-- Name: indikatory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.indikatory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.indikatory_id_seq OWNER TO postgres;

--
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 255
-- Name: indikatory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.indikatory_id_seq OWNED BY public.indikatory.id;


--
-- TOC entry 232 (class 1259 OID 16453)
-- Name: kabelaz; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kabelaz (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.kabelaz OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16452)
-- Name: kabelaz_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.kabelaz_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.kabelaz_id_seq OWNER TO postgres;

--
-- TOC entry 5127 (class 0 OID 0)
-- Dependencies: 231
-- Name: kabelaz_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.kabelaz_id_seq OWNED BY public.kabelaz.id;


--
-- TOC entry 242 (class 1259 OID 16498)
-- Name: komunikatory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.komunikatory (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.komunikatory OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 16497)
-- Name: komunikatory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.komunikatory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.komunikatory_id_seq OWNER TO postgres;

--
-- TOC entry 5130 (class 0 OID 0)
-- Dependencies: 241
-- Name: komunikatory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.komunikatory_id_seq OWNED BY public.komunikatory.id;


--
-- TOC entry 236 (class 1259 OID 16471)
-- Name: podlahove_krabice; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.podlahove_krabice (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.podlahove_krabice OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 16470)
-- Name: podlahove_krabice_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.podlahove_krabice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.podlahove_krabice_id_seq OWNER TO postgres;

--
-- TOC entry 5133 (class 0 OID 0)
-- Dependencies: 235
-- Name: podlahove_krabice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.podlahove_krabice_id_seq OWNED BY public.podlahove_krabice.id;


--
-- TOC entry 252 (class 1259 OID 16543)
-- Name: pohybove_detektory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pohybove_detektory (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.pohybove_detektory OWNER TO postgres;

--
-- TOC entry 251 (class 1259 OID 16542)
-- Name: pohybove_detektory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pohybove_detektory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pohybove_detektory_id_seq OWNER TO postgres;

--
-- TOC entry 5136 (class 0 OID 0)
-- Dependencies: 251
-- Name: pohybove_detektory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pohybove_detektory_id_seq OWNED BY public.pohybove_detektory.id;


--
-- TOC entry 246 (class 1259 OID 16516)
-- Name: pristupove_moduly; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pristupove_moduly (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.pristupove_moduly OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 16515)
-- Name: pristupove_moduly_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pristupove_moduly_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pristupove_moduly_id_seq OWNER TO postgres;

--
-- TOC entry 5139 (class 0 OID 0)
-- Dependencies: 245
-- Name: pristupove_moduly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pristupove_moduly_id_seq OWNED BY public.pristupove_moduly.id;


--
-- TOC entry 240 (class 1259 OID 16489)
-- Name: radiove_moduly; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.radiove_moduly (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.radiove_moduly OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 16488)
-- Name: radiove_moduly_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.radiove_moduly_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.radiove_moduly_id_seq OWNER TO postgres;

--
-- TOC entry 5142 (class 0 OID 0)
-- Dependencies: 239
-- Name: radiove_moduly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.radiove_moduly_id_seq OWNED BY public.radiove_moduly.id;


--
-- TOC entry 254 (class 1259 OID 16552)
-- Name: rele; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rele (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.rele OWNER TO postgres;

--
-- TOC entry 253 (class 1259 OID 16551)
-- Name: rele_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rele_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rele_id_seq OWNER TO postgres;

--
-- TOC entry 5145 (class 0 OID 0)
-- Dependencies: 253
-- Name: rele_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rele_id_seq OWNED BY public.rele.id;


--
-- TOC entry 244 (class 1259 OID 16507)
-- Name: rozhrania; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rozhrania (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.rozhrania OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 16506)
-- Name: rozhrania_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rozhrania_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rozhrania_id_seq OWNER TO postgres;

--
-- TOC entry 5148 (class 0 OID 0)
-- Dependencies: 243
-- Name: rozhrania_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rozhrania_id_seq OWNED BY public.rozhrania.id;


--
-- TOC entry 218 (class 1259 OID 16390)
-- Name: rozvadzace; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rozvadzace (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.rozvadzace OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16389)
-- Name: rozvadzace_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rozvadzace_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rozvadzace_id_seq OWNER TO postgres;

--
-- TOC entry 5151 (class 0 OID 0)
-- Dependencies: 217
-- Name: rozvadzace_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rozvadzace_id_seq OWNED BY public.rozvadzace.id;


--
-- TOC entry 248 (class 1259 OID 16525)
-- Name: sireny_vnutorne; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sireny_vnutorne (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.sireny_vnutorne OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 16524)
-- Name: sireny_vnutorne_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sireny_vnutorne_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sireny_vnutorne_id_seq OWNER TO postgres;

--
-- TOC entry 5154 (class 0 OID 0)
-- Dependencies: 247
-- Name: sireny_vnutorne_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sireny_vnutorne_id_seq OWNED BY public.sireny_vnutorne.id;


--
-- TOC entry 250 (class 1259 OID 16534)
-- Name: sireny_vonkajsie; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sireny_vonkajsie (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.sireny_vonkajsie OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 16533)
-- Name: sireny_vonkajsie_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sireny_vonkajsie_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sireny_vonkajsie_id_seq OWNER TO postgres;

--
-- TOC entry 5157 (class 0 OID 0)
-- Dependencies: 249
-- Name: sireny_vonkajsie_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sireny_vonkajsie_id_seq OWNED BY public.sireny_vonkajsie.id;


--
-- TOC entry 224 (class 1259 OID 16417)
-- Name: switche; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.switche (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.switche OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16416)
-- Name: switche_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.switche_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.switche_id_seq OWNER TO postgres;

--
-- TOC entry 5160 (class 0 OID 0)
-- Dependencies: 223
-- Name: switche_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.switche_id_seq OWNED BY public.switche.id;


--
-- TOC entry 238 (class 1259 OID 16480)
-- Name: ustredne; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ustredne (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.ustredne OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 16479)
-- Name: ustredne_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ustredne_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ustredne_id_seq OWNER TO postgres;

--
-- TOC entry 5163 (class 0 OID 0)
-- Dependencies: 237
-- Name: ustredne_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ustredne_id_seq OWNED BY public.ustredne.id;


--
-- TOC entry 220 (class 1259 OID 16399)
-- Name: vybava_rozvadzacov; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vybava_rozvadzacov (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.vybava_rozvadzacov OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16398)
-- Name: vybava_rozvadzacov_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vybava_rozvadzacov_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vybava_rozvadzacov_id_seq OWNER TO postgres;

--
-- TOC entry 5166 (class 0 OID 0)
-- Dependencies: 219
-- Name: vybava_rozvadzacov_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vybava_rozvadzacov_id_seq OWNED BY public.vybava_rozvadzacov.id;


--
-- TOC entry 222 (class 1259 OID 16408)
-- Name: wifi_ap; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wifi_ap (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.wifi_ap OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16407)
-- Name: wifi_ap_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wifi_ap_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wifi_ap_id_seq OWNER TO postgres;

--
-- TOC entry 5169 (class 0 OID 0)
-- Dependencies: 221
-- Name: wifi_ap_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wifi_ap_id_seq OWNED BY public.wifi_ap.id;


--
-- TOC entry 226 (class 1259 OID 16426)
-- Name: zalozne_zdroje; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zalozne_zdroje (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.zalozne_zdroje OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16435)
-- Name: zalozne_zdroje_battery_packy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zalozne_zdroje_battery_packy (
    id integer NOT NULL,
    nazov character varying(255) NOT NULL,
    jednotka character varying(50),
    pocet integer NOT NULL,
    dodavatel character varying(255),
    odkaz text,
    koeficient numeric(10,2),
    nakup_material numeric(10,2)
);


ALTER TABLE public.zalozne_zdroje_battery_packy OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16434)
-- Name: zalozne_zdroje_battery_packy_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zalozne_zdroje_battery_packy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zalozne_zdroje_battery_packy_id_seq OWNER TO postgres;

--
-- TOC entry 5173 (class 0 OID 0)
-- Dependencies: 227
-- Name: zalozne_zdroje_battery_packy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zalozne_zdroje_battery_packy_id_seq OWNED BY public.zalozne_zdroje_battery_packy.id;


--
-- TOC entry 225 (class 1259 OID 16425)
-- Name: zalozne_zdroje_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zalozne_zdroje_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zalozne_zdroje_id_seq OWNER TO postgres;

--
-- TOC entry 5175 (class 0 OID 0)
-- Dependencies: 225
-- Name: zalozne_zdroje_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zalozne_zdroje_id_seq OWNED BY public.zalozne_zdroje.id;


--
-- TOC entry 4849 (class 2604 OID 16447)
-- Name: battery_packy id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battery_packy ALTER COLUMN id SET DEFAULT nextval('public.battery_packy_id_seq'::regclass);


--
-- TOC entry 4851 (class 2604 OID 16465)
-- Name: datove_zasuvky id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.datove_zasuvky ALTER COLUMN id SET DEFAULT nextval('public.datove_zasuvky_id_seq'::regclass);


--
-- TOC entry 4862 (class 2604 OID 16564)
-- Name: indikatory id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indikatory ALTER COLUMN id SET DEFAULT nextval('public.indikatory_id_seq'::regclass);


--
-- TOC entry 4850 (class 2604 OID 16456)
-- Name: kabelaz id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kabelaz ALTER COLUMN id SET DEFAULT nextval('public.kabelaz_id_seq'::regclass);


--
-- TOC entry 4855 (class 2604 OID 16501)
-- Name: komunikatory id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.komunikatory ALTER COLUMN id SET DEFAULT nextval('public.komunikatory_id_seq'::regclass);


--
-- TOC entry 4852 (class 2604 OID 16474)
-- Name: podlahove_krabice id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.podlahove_krabice ALTER COLUMN id SET DEFAULT nextval('public.podlahove_krabice_id_seq'::regclass);


--
-- TOC entry 4860 (class 2604 OID 16546)
-- Name: pohybove_detektory id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pohybove_detektory ALTER COLUMN id SET DEFAULT nextval('public.pohybove_detektory_id_seq'::regclass);


--
-- TOC entry 4857 (class 2604 OID 16519)
-- Name: pristupove_moduly id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pristupove_moduly ALTER COLUMN id SET DEFAULT nextval('public.pristupove_moduly_id_seq'::regclass);


--
-- TOC entry 4854 (class 2604 OID 16492)
-- Name: radiove_moduly id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiove_moduly ALTER COLUMN id SET DEFAULT nextval('public.radiove_moduly_id_seq'::regclass);


--
-- TOC entry 4861 (class 2604 OID 16555)
-- Name: rele id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rele ALTER COLUMN id SET DEFAULT nextval('public.rele_id_seq'::regclass);


--
-- TOC entry 4856 (class 2604 OID 16510)
-- Name: rozhrania id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rozhrania ALTER COLUMN id SET DEFAULT nextval('public.rozhrania_id_seq'::regclass);


--
-- TOC entry 4843 (class 2604 OID 16393)
-- Name: rozvadzace id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rozvadzace ALTER COLUMN id SET DEFAULT nextval('public.rozvadzace_id_seq'::regclass);


--
-- TOC entry 4858 (class 2604 OID 16528)
-- Name: sireny_vnutorne id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sireny_vnutorne ALTER COLUMN id SET DEFAULT nextval('public.sireny_vnutorne_id_seq'::regclass);


--
-- TOC entry 4859 (class 2604 OID 16537)
-- Name: sireny_vonkajsie id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sireny_vonkajsie ALTER COLUMN id SET DEFAULT nextval('public.sireny_vonkajsie_id_seq'::regclass);


--
-- TOC entry 4846 (class 2604 OID 16420)
-- Name: switche id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.switche ALTER COLUMN id SET DEFAULT nextval('public.switche_id_seq'::regclass);


--
-- TOC entry 4853 (class 2604 OID 16483)
-- Name: ustredne id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ustredne ALTER COLUMN id SET DEFAULT nextval('public.ustredne_id_seq'::regclass);


--
-- TOC entry 4844 (class 2604 OID 16402)
-- Name: vybava_rozvadzacov id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vybava_rozvadzacov ALTER COLUMN id SET DEFAULT nextval('public.vybava_rozvadzacov_id_seq'::regclass);


--
-- TOC entry 4845 (class 2604 OID 16411)
-- Name: wifi_ap id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wifi_ap ALTER COLUMN id SET DEFAULT nextval('public.wifi_ap_id_seq'::regclass);


--
-- TOC entry 4847 (class 2604 OID 16429)
-- Name: zalozne_zdroje id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zalozne_zdroje ALTER COLUMN id SET DEFAULT nextval('public.zalozne_zdroje_id_seq'::regclass);


--
-- TOC entry 4848 (class 2604 OID 16438)
-- Name: zalozne_zdroje_battery_packy id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zalozne_zdroje_battery_packy ALTER COLUMN id SET DEFAULT nextval('public.zalozne_zdroje_battery_packy_id_seq'::regclass);


--
-- TOC entry 5109 (class 0 OID 16586)
-- Dependencies: 257
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: admin_user
--

COPY public.audit_log (tabulka, akcia, vykonal, datum, povodny_zaznam, novy_zaznam) FROM stdin;
indikatory	INSERT	admin_user	2025-03-25 10:36:31.596829	\N	{"id": 1, "cena": 12.50, "nazov": "Izol cia stropu miner lnou vlnou", "odkaz": "https://www.izoltech.sk/produkty/izolacia-stropu", "pocet": 100, "jednotka": "m2", "dodavatel": "IzolTech s.r.o.", "koeficient": 1.20, "nakup_material": 8.50}
wifi_ap	INSERT	app_user	2025-03-25 11:01:15.988039	\N	{"id": 2, "cena": 1.00, "nazov": "dw", "odkaz": "dw", "pocet": 1, "jednotka": "wd", "dodavatel": "wdw", "koeficient": null, "nakup_material": 1.00}
wifi_ap	DELETE	app_user	2025-03-25 11:06:45.124168	{"id": 2, "cena": 1.00, "nazov": "dw", "odkaz": "dw", "pocet": 1, "jednotka": "wd", "dodavatel": "wdw", "koeficient": null, "nakup_material": 1.00}	\N
wifi_ap	INSERT	app_user	2025-03-25 15:53:24.696729	\N	{"id": 3, "cena": 1.00, "nazov": "test", "odkaz": "dwad", "pocet": 1, "jednotka": "ks", "dodavatel": "dwa", "koeficient": null, "nakup_material": 1.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:01:17.210594	\N	{"id": 1, "cena": 10.00, "nazov": "test2A", "odkaz": "http://odkaz2a", "pocet": 1, "jednotka": "ks", "dodavatel": "Doda A", "koeficient": 1.20, "nakup_material": 8.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:01:17.210594	\N	{"id": 2, "cena": 11.00, "nazov": "test2B", "odkaz": "http://odkaz2b", "pocet": 2, "jednotka": "ks", "dodavatel": "Doda B", "koeficient": 1.30, "nakup_material": 8.50}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:01:17.210594	\N	{"id": 3, "cena": 12.00, "nazov": "test2C", "odkaz": "http://odkaz2c", "pocet": 3, "jednotka": "ks", "dodavatel": "Doda C", "koeficient": 1.10, "nakup_material": 9.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:01:17.210594	\N	{"id": 4, "cena": 13.00, "nazov": "test2D", "odkaz": "http://odkaz2d", "pocet": 4, "jednotka": "ks", "dodavatel": "Doda D", "koeficient": 1.25, "nakup_material": 9.50}
rozvadzace	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 13, "cena": 100.00, "nazov": "test1A", "odkaz": "http://odkaz1a", "pocet": 1, "jednotka": "ks", "dodavatel": "Dodavatel A", "koeficient": 1.20, "nakup_material": 80.00}
rozvadzace	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 14, "cena": 110.00, "nazov": "test1B", "odkaz": "http://odkaz1b", "pocet": 2, "jednotka": "ks", "dodavatel": "Dodavatel B", "koeficient": 1.30, "nakup_material": 85.00}
rozvadzace	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 15, "cena": 120.00, "nazov": "test1C", "odkaz": "http://odkaz1c", "pocet": 3, "jednotka": "ks", "dodavatel": "Dodavatel C", "koeficient": 1.10, "nakup_material": 90.00}
rozvadzace	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 16, "cena": 130.00, "nazov": "test1D", "odkaz": "http://odkaz1d", "pocet": 4, "jednotka": "ks", "dodavatel": "Dodavatel D", "koeficient": 1.25, "nakup_material": 95.00}
wifi_ap	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 20.00, "nazov": "test3A", "odkaz": "http://odkaz3a", "pocet": 1, "jednotka": "ks", "dodavatel": "WiFi A", "koeficient": 1.20, "nakup_material": 18.00}
wifi_ap	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 5, "cena": 21.00, "nazov": "test3B", "odkaz": "http://odkaz3b", "pocet": 2, "jednotka": "ks", "dodavatel": "WiFi B", "koeficient": 1.30, "nakup_material": 18.50}
wifi_ap	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 6, "cena": 22.00, "nazov": "test3C", "odkaz": "http://odkaz3c", "pocet": 3, "jednotka": "ks", "dodavatel": "WiFi C", "koeficient": 1.10, "nakup_material": 19.00}
wifi_ap	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 7, "cena": 23.00, "nazov": "test3D", "odkaz": "http://odkaz3d", "pocet": 4, "jednotka": "ks", "dodavatel": "WiFi D", "koeficient": 1.25, "nakup_material": 19.50}
switche	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 30.00, "nazov": "test4A", "odkaz": "http://odkaz4a", "pocet": 1, "jednotka": "ks", "dodavatel": "Switch A", "koeficient": 1.20, "nakup_material": 25.00}
switche	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 31.00, "nazov": "test4B", "odkaz": "http://odkaz4b", "pocet": 2, "jednotka": "ks", "dodavatel": "Switch B", "koeficient": 1.30, "nakup_material": 26.00}
switche	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 32.00, "nazov": "test4C", "odkaz": "http://odkaz4c", "pocet": 3, "jednotka": "ks", "dodavatel": "Switch C", "koeficient": 1.10, "nakup_material": 27.00}
switche	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 33.00, "nazov": "test4D", "odkaz": "http://odkaz4d", "pocet": 4, "jednotka": "ks", "dodavatel": "Switch D", "koeficient": 1.25, "nakup_material": 28.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 40.00, "nazov": "test5A", "odkaz": "http://odkaz5a", "pocet": 1, "jednotka": "ks", "dodavatel": "Zaloha A", "koeficient": 1.20, "nakup_material": 38.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 41.00, "nazov": "test5B", "odkaz": "http://odkaz5b", "pocet": 2, "jednotka": "ks", "dodavatel": "Zaloha B", "koeficient": 1.30, "nakup_material": 39.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 42.00, "nazov": "test5C", "odkaz": "http://odkaz5c", "pocet": 3, "jednotka": "ks", "dodavatel": "Zaloha C", "koeficient": 1.10, "nakup_material": 40.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 43.00, "nazov": "test5D", "odkaz": "http://odkaz5d", "pocet": 4, "jednotka": "ks", "dodavatel": "Zaloha D", "koeficient": 1.25, "nakup_material": 41.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 50.00, "nazov": "test6A", "odkaz": "http://odkaz6a", "pocet": 1, "jednotka": "ks", "dodavatel": "Batt A", "koeficient": 1.20, "nakup_material": 48.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 51.00, "nazov": "test6B", "odkaz": "http://odkaz6b", "pocet": 2, "jednotka": "ks", "dodavatel": "Batt B", "koeficient": 1.30, "nakup_material": 49.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 52.00, "nazov": "test6C", "odkaz": "http://odkaz6c", "pocet": 3, "jednotka": "ks", "dodavatel": "Batt C", "koeficient": 1.10, "nakup_material": 50.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 53.00, "nazov": "test6D", "odkaz": "http://odkaz6d", "pocet": 4, "jednotka": "ks", "dodavatel": "Batt D", "koeficient": 1.25, "nakup_material": 51.00}
battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 60.00, "nazov": "test7A", "odkaz": "http://odkaz7a", "pocet": 1, "jednotka": "ks", "dodavatel": "BP A", "koeficient": 1.20, "nakup_material": 58.00}
battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 61.00, "nazov": "test7B", "odkaz": "http://odkaz7b", "pocet": 2, "jednotka": "ks", "dodavatel": "BP B", "koeficient": 1.30, "nakup_material": 59.00}
battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 62.00, "nazov": "test7C", "odkaz": "http://odkaz7c", "pocet": 3, "jednotka": "ks", "dodavatel": "BP C", "koeficient": 1.10, "nakup_material": 60.00}
battery_packy	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 63.00, "nazov": "test7D", "odkaz": "http://odkaz7d", "pocet": 4, "jednotka": "ks", "dodavatel": "BP D", "koeficient": 1.25, "nakup_material": 61.00}
kabelaz	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 15.00, "nazov": "test8A", "odkaz": "http://odkaz8a", "pocet": 10, "jednotka": "m", "dodavatel": "Kabel A", "koeficient": 1.20, "nakup_material": 13.00}
kabelaz	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 16.00, "nazov": "test8B", "odkaz": "http://odkaz8b", "pocet": 20, "jednotka": "m", "dodavatel": "Kabel B", "koeficient": 1.30, "nakup_material": 13.50}
kabelaz	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 17.00, "nazov": "test8C", "odkaz": "http://odkaz8c", "pocet": 30, "jednotka": "m", "dodavatel": "Kabel C", "koeficient": 1.10, "nakup_material": 14.00}
kabelaz	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 18.00, "nazov": "test8D", "odkaz": "http://odkaz8d", "pocet": 40, "jednotka": "m", "dodavatel": "Kabel D", "koeficient": 1.25, "nakup_material": 14.50}
datove_zasuvky	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 5.00, "nazov": "test9A", "odkaz": "http://odkaz9a", "pocet": 1, "jednotka": "ks", "dodavatel": "DZ A", "koeficient": 1.20, "nakup_material": 4.00}
datove_zasuvky	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 5.50, "nazov": "test9B", "odkaz": "http://odkaz9b", "pocet": 2, "jednotka": "ks", "dodavatel": "DZ B", "koeficient": 1.30, "nakup_material": 4.20}
datove_zasuvky	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 6.00, "nazov": "test9C", "odkaz": "http://odkaz9c", "pocet": 3, "jednotka": "ks", "dodavatel": "DZ C", "koeficient": 1.10, "nakup_material": 4.50}
datove_zasuvky	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 6.50, "nazov": "test9D", "odkaz": "http://odkaz9d", "pocet": 4, "jednotka": "ks", "dodavatel": "DZ D", "koeficient": 1.25, "nakup_material": 4.80}
podlahove_krabice	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 1, "cena": 8.00, "nazov": "test10A", "odkaz": "http://odkaz10a", "pocet": 1, "jednotka": "ks", "dodavatel": "PK A", "koeficient": 1.20, "nakup_material": 6.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 2, "cena": 9.00, "nazov": "test10B", "odkaz": "http://odkaz10b", "pocet": 2, "jednotka": "ks", "dodavatel": "PK B", "koeficient": 1.30, "nakup_material": 6.50}
podlahove_krabice	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 3, "cena": 10.00, "nazov": "test10C", "odkaz": "http://odkaz10c", "pocet": 3, "jednotka": "ks", "dodavatel": "PK C", "koeficient": 1.10, "nakup_material": 7.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:04:42.606737	\N	{"id": 4, "cena": 11.00, "nazov": "test10D", "odkaz": "http://odkaz10d", "pocet": 4, "jednotka": "ks", "dodavatel": "PK D", "koeficient": 1.25, "nakup_material": 7.50}
ustredne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 70.00, "nazov": "test11A", "odkaz": "http://odkaz11a", "pocet": 1, "jednotka": "ks", "dodavatel": "Ustredna A", "koeficient": 1.20, "nakup_material": 65.00}
ustredne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 71.00, "nazov": "test11B", "odkaz": "http://odkaz11b", "pocet": 2, "jednotka": "ks", "dodavatel": "Ustredna B", "koeficient": 1.30, "nakup_material": 66.00}
ustredne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 72.00, "nazov": "test11C", "odkaz": "http://odkaz11c", "pocet": 3, "jednotka": "ks", "dodavatel": "Ustredna C", "koeficient": 1.10, "nakup_material": 67.00}
ustredne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 73.00, "nazov": "test11D", "odkaz": "http://odkaz11d", "pocet": 4, "jednotka": "ks", "dodavatel": "Ustredna D", "koeficient": 1.25, "nakup_material": 68.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 80.00, "nazov": "test12A", "odkaz": "http://odkaz12a", "pocet": 1, "jednotka": "ks", "dodavatel": "Radio A", "koeficient": 1.20, "nakup_material": 75.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 81.00, "nazov": "test12B", "odkaz": "http://odkaz12b", "pocet": 2, "jednotka": "ks", "dodavatel": "Radio B", "koeficient": 1.30, "nakup_material": 76.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 82.00, "nazov": "test12C", "odkaz": "http://odkaz12c", "pocet": 3, "jednotka": "ks", "dodavatel": "Radio C", "koeficient": 1.10, "nakup_material": 77.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 83.00, "nazov": "test12D", "odkaz": "http://odkaz12d", "pocet": 4, "jednotka": "ks", "dodavatel": "Radio D", "koeficient": 1.25, "nakup_material": 78.00}
komunikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 90.00, "nazov": "test13A", "odkaz": "http://odkaz13a", "pocet": 1, "jednotka": "ks", "dodavatel": "Kom A", "koeficient": 1.20, "nakup_material": 85.00}
komunikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 91.00, "nazov": "test13B", "odkaz": "http://odkaz13b", "pocet": 2, "jednotka": "ks", "dodavatel": "Kom B", "koeficient": 1.30, "nakup_material": 86.00}
komunikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 92.00, "nazov": "test13C", "odkaz": "http://odkaz13c", "pocet": 3, "jednotka": "ks", "dodavatel": "Kom C", "koeficient": 1.10, "nakup_material": 87.00}
komunikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 93.00, "nazov": "test13D", "odkaz": "http://odkaz13d", "pocet": 4, "jednotka": "ks", "dodavatel": "Kom D", "koeficient": 1.25, "nakup_material": 88.00}
rozhrania	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 100.00, "nazov": "test14A", "odkaz": "http://odkaz14a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rozhranie A", "koeficient": 1.20, "nakup_material": 95.00}
rozhrania	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 101.00, "nazov": "test14B", "odkaz": "http://odkaz14b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rozhranie B", "koeficient": 1.30, "nakup_material": 96.00}
rozhrania	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 102.00, "nazov": "test14C", "odkaz": "http://odkaz14c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rozhranie C", "koeficient": 1.10, "nakup_material": 97.00}
rozhrania	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 103.00, "nazov": "test14D", "odkaz": "http://odkaz14d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rozhranie D", "koeficient": 1.25, "nakup_material": 98.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 110.00, "nazov": "test15A", "odkaz": "http://odkaz15a", "pocet": 1, "jednotka": "ks", "dodavatel": "Pristup A", "koeficient": 1.20, "nakup_material": 105.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 111.00, "nazov": "test15B", "odkaz": "http://odkaz15b", "pocet": 2, "jednotka": "ks", "dodavatel": "Pristup B", "koeficient": 1.30, "nakup_material": 106.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 112.00, "nazov": "test15C", "odkaz": "http://odkaz15c", "pocet": 3, "jednotka": "ks", "dodavatel": "Pristup C", "koeficient": 1.10, "nakup_material": 107.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 113.00, "nazov": "test15D", "odkaz": "http://odkaz15d", "pocet": 4, "jednotka": "ks", "dodavatel": "Pristup D", "koeficient": 1.25, "nakup_material": 108.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 50.00, "nazov": "test16A", "odkaz": "http://odkaz16a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena In A", "koeficient": 1.20, "nakup_material": 45.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 51.00, "nazov": "test16B", "odkaz": "http://odkaz16b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena In B", "koeficient": 1.30, "nakup_material": 46.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 52.00, "nazov": "test16C", "odkaz": "http://odkaz16c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena In C", "koeficient": 1.10, "nakup_material": 47.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 53.00, "nazov": "test16D", "odkaz": "http://odkaz16d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena In D", "koeficient": 1.25, "nakup_material": 48.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 60.00, "nazov": "test17A", "odkaz": "http://odkaz17a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena Out A", "koeficient": 1.20, "nakup_material": 55.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 61.00, "nazov": "test17B", "odkaz": "http://odkaz17b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena Out B", "koeficient": 1.30, "nakup_material": 56.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 62.00, "nazov": "test17C", "odkaz": "http://odkaz17c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena Out C", "koeficient": 1.10, "nakup_material": 57.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 63.00, "nazov": "test17D", "odkaz": "http://odkaz17d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena Out D", "koeficient": 1.25, "nakup_material": 58.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 20.00, "nazov": "test18A", "odkaz": "http://odkaz18a", "pocet": 1, "jednotka": "ks", "dodavatel": "Detektor A", "koeficient": 1.20, "nakup_material": 18.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 21.00, "nazov": "test18B", "odkaz": "http://odkaz18b", "pocet": 2, "jednotka": "ks", "dodavatel": "Detektor B", "koeficient": 1.30, "nakup_material": 19.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 22.00, "nazov": "test18C", "odkaz": "http://odkaz18c", "pocet": 3, "jednotka": "ks", "dodavatel": "Detektor C", "koeficient": 1.10, "nakup_material": 20.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 23.00, "nazov": "test18D", "odkaz": "http://odkaz18d", "pocet": 4, "jednotka": "ks", "dodavatel": "Detektor D", "koeficient": 1.25, "nakup_material": 21.00}
rele	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 1, "cena": 15.00, "nazov": "test19A", "odkaz": "http://odkaz19a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rele A", "koeficient": 1.20, "nakup_material": 13.00}
rele	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 16.00, "nazov": "test19B", "odkaz": "http://odkaz19b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rele B", "koeficient": 1.30, "nakup_material": 14.00}
rele	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 17.00, "nazov": "test19C", "odkaz": "http://odkaz19c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rele C", "koeficient": 1.10, "nakup_material": 15.00}
rele	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 18.00, "nazov": "test19D", "odkaz": "http://odkaz19d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rele D", "koeficient": 1.25, "nakup_material": 16.00}
indikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 2, "cena": 5.00, "nazov": "test20A", "odkaz": "http://odkaz20a", "pocet": 1, "jednotka": "ks", "dodavatel": "Indikator A", "koeficient": 1.20, "nakup_material": 4.00}
indikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 3, "cena": 5.50, "nazov": "test20B", "odkaz": "http://odkaz20b", "pocet": 2, "jednotka": "ks", "dodavatel": "Indikator B", "koeficient": 1.30, "nakup_material": 4.20}
indikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 4, "cena": 6.00, "nazov": "test20C", "odkaz": "http://odkaz20c", "pocet": 3, "jednotka": "ks", "dodavatel": "Indikator C", "koeficient": 1.10, "nakup_material": 4.50}
indikatory	INSERT	postgres	2025-03-26 22:05:58.784152	\N	{"id": 5, "cena": 6.50, "nazov": "test20D", "odkaz": "http://odkaz20d", "pocet": 4, "jednotka": "ks", "dodavatel": "Indikator D", "koeficient": 1.25, "nakup_material": 4.80}
rozvadzace	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 13, "cena": 100.00, "nazov": "test1A", "odkaz": "http://odkaz1a", "pocet": 1, "jednotka": "ks", "dodavatel": "Dodavatel A", "koeficient": 1.20, "nakup_material": 80.00}	\N
rozvadzace	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 14, "cena": 110.00, "nazov": "test1B", "odkaz": "http://odkaz1b", "pocet": 2, "jednotka": "ks", "dodavatel": "Dodavatel B", "koeficient": 1.30, "nakup_material": 85.00}	\N
rozvadzace	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 15, "cena": 120.00, "nazov": "test1C", "odkaz": "http://odkaz1c", "pocet": 3, "jednotka": "ks", "dodavatel": "Dodavatel C", "koeficient": 1.10, "nakup_material": 90.00}	\N
rozvadzace	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 16, "cena": 130.00, "nazov": "test1D", "odkaz": "http://odkaz1d", "pocet": 4, "jednotka": "ks", "dodavatel": "Dodavatel D", "koeficient": 1.25, "nakup_material": 95.00}	\N
vybava_rozvadzacov	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 10.00, "nazov": "test2A", "odkaz": "http://odkaz2a", "pocet": 1, "jednotka": "ks", "dodavatel": "Doda A", "koeficient": 1.20, "nakup_material": 8.00}	\N
vybava_rozvadzacov	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 11.00, "nazov": "test2B", "odkaz": "http://odkaz2b", "pocet": 2, "jednotka": "ks", "dodavatel": "Doda B", "koeficient": 1.30, "nakup_material": 8.50}	\N
vybava_rozvadzacov	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 12.00, "nazov": "test2C", "odkaz": "http://odkaz2c", "pocet": 3, "jednotka": "ks", "dodavatel": "Doda C", "koeficient": 1.10, "nakup_material": 9.00}	\N
vybava_rozvadzacov	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 13.00, "nazov": "test2D", "odkaz": "http://odkaz2d", "pocet": 4, "jednotka": "ks", "dodavatel": "Doda D", "koeficient": 1.25, "nakup_material": 9.50}	\N
wifi_ap	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 1.00, "nazov": "test", "odkaz": "dwad", "pocet": 1, "jednotka": "ks", "dodavatel": "dwa", "koeficient": null, "nakup_material": 1.00}	\N
wifi_ap	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 20.00, "nazov": "test3A", "odkaz": "http://odkaz3a", "pocet": 1, "jednotka": "ks", "dodavatel": "WiFi A", "koeficient": 1.20, "nakup_material": 18.00}	\N
wifi_ap	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 5, "cena": 21.00, "nazov": "test3B", "odkaz": "http://odkaz3b", "pocet": 2, "jednotka": "ks", "dodavatel": "WiFi B", "koeficient": 1.30, "nakup_material": 18.50}	\N
wifi_ap	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 6, "cena": 22.00, "nazov": "test3C", "odkaz": "http://odkaz3c", "pocet": 3, "jednotka": "ks", "dodavatel": "WiFi C", "koeficient": 1.10, "nakup_material": 19.00}	\N
wifi_ap	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 7, "cena": 23.00, "nazov": "test3D", "odkaz": "http://odkaz3d", "pocet": 4, "jednotka": "ks", "dodavatel": "WiFi D", "koeficient": 1.25, "nakup_material": 19.50}	\N
switche	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 30.00, "nazov": "test4A", "odkaz": "http://odkaz4a", "pocet": 1, "jednotka": "ks", "dodavatel": "Switch A", "koeficient": 1.20, "nakup_material": 25.00}	\N
switche	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 31.00, "nazov": "test4B", "odkaz": "http://odkaz4b", "pocet": 2, "jednotka": "ks", "dodavatel": "Switch B", "koeficient": 1.30, "nakup_material": 26.00}	\N
switche	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 32.00, "nazov": "test4C", "odkaz": "http://odkaz4c", "pocet": 3, "jednotka": "ks", "dodavatel": "Switch C", "koeficient": 1.10, "nakup_material": 27.00}	\N
switche	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 33.00, "nazov": "test4D", "odkaz": "http://odkaz4d", "pocet": 4, "jednotka": "ks", "dodavatel": "Switch D", "koeficient": 1.25, "nakup_material": 28.00}	\N
zalozne_zdroje	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 40.00, "nazov": "test5A", "odkaz": "http://odkaz5a", "pocet": 1, "jednotka": "ks", "dodavatel": "Zaloha A", "koeficient": 1.20, "nakup_material": 38.00}	\N
zalozne_zdroje	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 41.00, "nazov": "test5B", "odkaz": "http://odkaz5b", "pocet": 2, "jednotka": "ks", "dodavatel": "Zaloha B", "koeficient": 1.30, "nakup_material": 39.00}	\N
zalozne_zdroje	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 42.00, "nazov": "test5C", "odkaz": "http://odkaz5c", "pocet": 3, "jednotka": "ks", "dodavatel": "Zaloha C", "koeficient": 1.10, "nakup_material": 40.00}	\N
zalozne_zdroje	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 43.00, "nazov": "test5D", "odkaz": "http://odkaz5d", "pocet": 4, "jednotka": "ks", "dodavatel": "Zaloha D", "koeficient": 1.25, "nakup_material": 41.00}	\N
zalozne_zdroje_battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 50.00, "nazov": "test6A", "odkaz": "http://odkaz6a", "pocet": 1, "jednotka": "ks", "dodavatel": "Batt A", "koeficient": 1.20, "nakup_material": 48.00}	\N
zalozne_zdroje_battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 51.00, "nazov": "test6B", "odkaz": "http://odkaz6b", "pocet": 2, "jednotka": "ks", "dodavatel": "Batt B", "koeficient": 1.30, "nakup_material": 49.00}	\N
zalozne_zdroje_battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 52.00, "nazov": "test6C", "odkaz": "http://odkaz6c", "pocet": 3, "jednotka": "ks", "dodavatel": "Batt C", "koeficient": 1.10, "nakup_material": 50.00}	\N
zalozne_zdroje_battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 53.00, "nazov": "test6D", "odkaz": "http://odkaz6d", "pocet": 4, "jednotka": "ks", "dodavatel": "Batt D", "koeficient": 1.25, "nakup_material": 51.00}	\N
battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 60.00, "nazov": "test7A", "odkaz": "http://odkaz7a", "pocet": 1, "jednotka": "ks", "dodavatel": "BP A", "koeficient": 1.20, "nakup_material": 58.00}	\N
battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 61.00, "nazov": "test7B", "odkaz": "http://odkaz7b", "pocet": 2, "jednotka": "ks", "dodavatel": "BP B", "koeficient": 1.30, "nakup_material": 59.00}	\N
battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 62.00, "nazov": "test7C", "odkaz": "http://odkaz7c", "pocet": 3, "jednotka": "ks", "dodavatel": "BP C", "koeficient": 1.10, "nakup_material": 60.00}	\N
battery_packy	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 63.00, "nazov": "test7D", "odkaz": "http://odkaz7d", "pocet": 4, "jednotka": "ks", "dodavatel": "BP D", "koeficient": 1.25, "nakup_material": 61.00}	\N
kabelaz	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 15.00, "nazov": "test8A", "odkaz": "http://odkaz8a", "pocet": 10, "jednotka": "m", "dodavatel": "Kabel A", "koeficient": 1.20, "nakup_material": 13.00}	\N
kabelaz	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 16.00, "nazov": "test8B", "odkaz": "http://odkaz8b", "pocet": 20, "jednotka": "m", "dodavatel": "Kabel B", "koeficient": 1.30, "nakup_material": 13.50}	\N
kabelaz	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 17.00, "nazov": "test8C", "odkaz": "http://odkaz8c", "pocet": 30, "jednotka": "m", "dodavatel": "Kabel C", "koeficient": 1.10, "nakup_material": 14.00}	\N
kabelaz	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 18.00, "nazov": "test8D", "odkaz": "http://odkaz8d", "pocet": 40, "jednotka": "m", "dodavatel": "Kabel D", "koeficient": 1.25, "nakup_material": 14.50}	\N
datove_zasuvky	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 5.00, "nazov": "test9A", "odkaz": "http://odkaz9a", "pocet": 1, "jednotka": "ks", "dodavatel": "DZ A", "koeficient": 1.20, "nakup_material": 4.00}	\N
datove_zasuvky	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 5.50, "nazov": "test9B", "odkaz": "http://odkaz9b", "pocet": 2, "jednotka": "ks", "dodavatel": "DZ B", "koeficient": 1.30, "nakup_material": 4.20}	\N
datove_zasuvky	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 6.00, "nazov": "test9C", "odkaz": "http://odkaz9c", "pocet": 3, "jednotka": "ks", "dodavatel": "DZ C", "koeficient": 1.10, "nakup_material": 4.50}	\N
datove_zasuvky	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 6.50, "nazov": "test9D", "odkaz": "http://odkaz9d", "pocet": 4, "jednotka": "ks", "dodavatel": "DZ D", "koeficient": 1.25, "nakup_material": 4.80}	\N
podlahove_krabice	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 8.00, "nazov": "test10A", "odkaz": "http://odkaz10a", "pocet": 1, "jednotka": "ks", "dodavatel": "PK A", "koeficient": 1.20, "nakup_material": 6.00}	\N
podlahove_krabice	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 9.00, "nazov": "test10B", "odkaz": "http://odkaz10b", "pocet": 2, "jednotka": "ks", "dodavatel": "PK B", "koeficient": 1.30, "nakup_material": 6.50}	\N
podlahove_krabice	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 10.00, "nazov": "test10C", "odkaz": "http://odkaz10c", "pocet": 3, "jednotka": "ks", "dodavatel": "PK C", "koeficient": 1.10, "nakup_material": 7.00}	\N
podlahove_krabice	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 11.00, "nazov": "test10D", "odkaz": "http://odkaz10d", "pocet": 4, "jednotka": "ks", "dodavatel": "PK D", "koeficient": 1.25, "nakup_material": 7.50}	\N
ustredne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 70.00, "nazov": "test11A", "odkaz": "http://odkaz11a", "pocet": 1, "jednotka": "ks", "dodavatel": "Ustredna A", "koeficient": 1.20, "nakup_material": 65.00}	\N
ustredne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 71.00, "nazov": "test11B", "odkaz": "http://odkaz11b", "pocet": 2, "jednotka": "ks", "dodavatel": "Ustredna B", "koeficient": 1.30, "nakup_material": 66.00}	\N
ustredne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 72.00, "nazov": "test11C", "odkaz": "http://odkaz11c", "pocet": 3, "jednotka": "ks", "dodavatel": "Ustredna C", "koeficient": 1.10, "nakup_material": 67.00}	\N
ustredne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 73.00, "nazov": "test11D", "odkaz": "http://odkaz11d", "pocet": 4, "jednotka": "ks", "dodavatel": "Ustredna D", "koeficient": 1.25, "nakup_material": 68.00}	\N
radiove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 80.00, "nazov": "test12A", "odkaz": "http://odkaz12a", "pocet": 1, "jednotka": "ks", "dodavatel": "Radio A", "koeficient": 1.20, "nakup_material": 75.00}	\N
radiove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 81.00, "nazov": "test12B", "odkaz": "http://odkaz12b", "pocet": 2, "jednotka": "ks", "dodavatel": "Radio B", "koeficient": 1.30, "nakup_material": 76.00}	\N
radiove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 82.00, "nazov": "test12C", "odkaz": "http://odkaz12c", "pocet": 3, "jednotka": "ks", "dodavatel": "Radio C", "koeficient": 1.10, "nakup_material": 77.00}	\N
radiove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 83.00, "nazov": "test12D", "odkaz": "http://odkaz12d", "pocet": 4, "jednotka": "ks", "dodavatel": "Radio D", "koeficient": 1.25, "nakup_material": 78.00}	\N
komunikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 90.00, "nazov": "test13A", "odkaz": "http://odkaz13a", "pocet": 1, "jednotka": "ks", "dodavatel": "Kom A", "koeficient": 1.20, "nakup_material": 85.00}	\N
komunikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 91.00, "nazov": "test13B", "odkaz": "http://odkaz13b", "pocet": 2, "jednotka": "ks", "dodavatel": "Kom B", "koeficient": 1.30, "nakup_material": 86.00}	\N
komunikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 92.00, "nazov": "test13C", "odkaz": "http://odkaz13c", "pocet": 3, "jednotka": "ks", "dodavatel": "Kom C", "koeficient": 1.10, "nakup_material": 87.00}	\N
komunikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 93.00, "nazov": "test13D", "odkaz": "http://odkaz13d", "pocet": 4, "jednotka": "ks", "dodavatel": "Kom D", "koeficient": 1.25, "nakup_material": 88.00}	\N
rozhrania	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 100.00, "nazov": "test14A", "odkaz": "http://odkaz14a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rozhranie A", "koeficient": 1.20, "nakup_material": 95.00}	\N
rozhrania	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 101.00, "nazov": "test14B", "odkaz": "http://odkaz14b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rozhranie B", "koeficient": 1.30, "nakup_material": 96.00}	\N
rozhrania	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 102.00, "nazov": "test14C", "odkaz": "http://odkaz14c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rozhranie C", "koeficient": 1.10, "nakup_material": 97.00}	\N
rozhrania	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 103.00, "nazov": "test14D", "odkaz": "http://odkaz14d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rozhranie D", "koeficient": 1.25, "nakup_material": 98.00}	\N
pristupove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 110.00, "nazov": "test15A", "odkaz": "http://odkaz15a", "pocet": 1, "jednotka": "ks", "dodavatel": "Pristup A", "koeficient": 1.20, "nakup_material": 105.00}	\N
pristupove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 111.00, "nazov": "test15B", "odkaz": "http://odkaz15b", "pocet": 2, "jednotka": "ks", "dodavatel": "Pristup B", "koeficient": 1.30, "nakup_material": 106.00}	\N
pristupove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 112.00, "nazov": "test15C", "odkaz": "http://odkaz15c", "pocet": 3, "jednotka": "ks", "dodavatel": "Pristup C", "koeficient": 1.10, "nakup_material": 107.00}	\N
pristupove_moduly	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 113.00, "nazov": "test15D", "odkaz": "http://odkaz15d", "pocet": 4, "jednotka": "ks", "dodavatel": "Pristup D", "koeficient": 1.25, "nakup_material": 108.00}	\N
sireny_vnutorne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 50.00, "nazov": "test16A", "odkaz": "http://odkaz16a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena In A", "koeficient": 1.20, "nakup_material": 45.00}	\N
sireny_vnutorne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 51.00, "nazov": "test16B", "odkaz": "http://odkaz16b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena In B", "koeficient": 1.30, "nakup_material": 46.00}	\N
sireny_vnutorne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 52.00, "nazov": "test16C", "odkaz": "http://odkaz16c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena In C", "koeficient": 1.10, "nakup_material": 47.00}	\N
sireny_vnutorne	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 53.00, "nazov": "test16D", "odkaz": "http://odkaz16d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena In D", "koeficient": 1.25, "nakup_material": 48.00}	\N
sireny_vonkajsie	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 60.00, "nazov": "test17A", "odkaz": "http://odkaz17a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena Out A", "koeficient": 1.20, "nakup_material": 55.00}	\N
sireny_vonkajsie	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 61.00, "nazov": "test17B", "odkaz": "http://odkaz17b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena Out B", "koeficient": 1.30, "nakup_material": 56.00}	\N
sireny_vonkajsie	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 62.00, "nazov": "test17C", "odkaz": "http://odkaz17c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena Out C", "koeficient": 1.10, "nakup_material": 57.00}	\N
sireny_vonkajsie	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 63.00, "nazov": "test17D", "odkaz": "http://odkaz17d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena Out D", "koeficient": 1.25, "nakup_material": 58.00}	\N
pohybove_detektory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 20.00, "nazov": "test18A", "odkaz": "http://odkaz18a", "pocet": 1, "jednotka": "ks", "dodavatel": "Detektor A", "koeficient": 1.20, "nakup_material": 18.00}	\N
pohybove_detektory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 21.00, "nazov": "test18B", "odkaz": "http://odkaz18b", "pocet": 2, "jednotka": "ks", "dodavatel": "Detektor B", "koeficient": 1.30, "nakup_material": 19.00}	\N
pohybove_detektory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 22.00, "nazov": "test18C", "odkaz": "http://odkaz18c", "pocet": 3, "jednotka": "ks", "dodavatel": "Detektor C", "koeficient": 1.10, "nakup_material": 20.00}	\N
pohybove_detektory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 23.00, "nazov": "test18D", "odkaz": "http://odkaz18d", "pocet": 4, "jednotka": "ks", "dodavatel": "Detektor D", "koeficient": 1.25, "nakup_material": 21.00}	\N
rele	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 15.00, "nazov": "test19A", "odkaz": "http://odkaz19a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rele A", "koeficient": 1.20, "nakup_material": 13.00}	\N
rele	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 16.00, "nazov": "test19B", "odkaz": "http://odkaz19b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rele B", "koeficient": 1.30, "nakup_material": 14.00}	\N
rele	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 17.00, "nazov": "test19C", "odkaz": "http://odkaz19c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rele C", "koeficient": 1.10, "nakup_material": 15.00}	\N
rele	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 18.00, "nazov": "test19D", "odkaz": "http://odkaz19d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rele D", "koeficient": 1.25, "nakup_material": 16.00}	\N
indikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 1, "cena": 12.50, "nazov": "Izol cia stropu miner lnou vlnou", "odkaz": "https://www.izoltech.sk/produkty/izolacia-stropu", "pocet": 100, "jednotka": "m2", "dodavatel": "IzolTech s.r.o.", "koeficient": 1.20, "nakup_material": 8.50}	\N
indikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 2, "cena": 5.00, "nazov": "test20A", "odkaz": "http://odkaz20a", "pocet": 1, "jednotka": "ks", "dodavatel": "Indikator A", "koeficient": 1.20, "nakup_material": 4.00}	\N
indikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 3, "cena": 5.50, "nazov": "test20B", "odkaz": "http://odkaz20b", "pocet": 2, "jednotka": "ks", "dodavatel": "Indikator B", "koeficient": 1.30, "nakup_material": 4.20}	\N
indikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 4, "cena": 6.00, "nazov": "test20C", "odkaz": "http://odkaz20c", "pocet": 3, "jednotka": "ks", "dodavatel": "Indikator C", "koeficient": 1.10, "nakup_material": 4.50}	\N
indikatory	DELETE	postgres	2025-03-26 22:07:40.357124	{"id": 5, "cena": 6.50, "nazov": "test20D", "odkaz": "http://odkaz20d", "pocet": 4, "jednotka": "ks", "dodavatel": "Indikator D", "koeficient": 1.25, "nakup_material": 4.80}	\N
rozvadzace	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 17, "cena": 15.00, "nazov": "test1A", "odkaz": "http://odkaztest1a", "pocet": 1, "jednotka": "ks", "dodavatel": "Dodavatel A", "koeficient": 1.20, "nakup_material": 12.00}
rozvadzace	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 18, "cena": 15.00, "nazov": "test1B", "odkaz": "http://odkaztest1b", "pocet": 2, "jednotka": "ks", "dodavatel": "Dodavatel B", "koeficient": 1.30, "nakup_material": 12.00}
rozvadzace	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 19, "cena": 15.00, "nazov": "test1C", "odkaz": "http://odkaztest1c", "pocet": 3, "jednotka": "ks", "dodavatel": "Dodavatel C", "koeficient": 1.10, "nakup_material": 12.00}
rozvadzace	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 20, "cena": 15.00, "nazov": "test1D", "odkaz": "http://odkaztest1d", "pocet": 4, "jednotka": "ks", "dodavatel": "Dodavatel D", "koeficient": 1.25, "nakup_material": 12.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 5, "cena": 20.00, "nazov": "test2A", "odkaz": "http://odkaztest2a", "pocet": 1, "jednotka": "ks", "dodavatel": "Dodavatel A", "koeficient": 1.20, "nakup_material": 16.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 6, "cena": 20.00, "nazov": "test2B", "odkaz": "http://odkaztest2b", "pocet": 2, "jednotka": "ks", "dodavatel": "Dodavatel B", "koeficient": 1.30, "nakup_material": 16.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 7, "cena": 20.00, "nazov": "test2C", "odkaz": "http://odkaztest2c", "pocet": 3, "jednotka": "ks", "dodavatel": "Dodavatel C", "koeficient": 1.10, "nakup_material": 16.00}
vybava_rozvadzacov	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 8, "cena": 20.00, "nazov": "test2D", "odkaz": "http://odkaztest2d", "pocet": 4, "jednotka": "ks", "dodavatel": "Dodavatel D", "koeficient": 1.25, "nakup_material": 16.00}
wifi_ap	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 8, "cena": 25.00, "nazov": "test3A", "odkaz": "http://odkaztest3a", "pocet": 1, "jednotka": "ks", "dodavatel": "WiFi A", "koeficient": 1.20, "nakup_material": 20.00}
wifi_ap	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 9, "cena": 25.00, "nazov": "test3B", "odkaz": "http://odkaztest3b", "pocet": 2, "jednotka": "ks", "dodavatel": "WiFi B", "koeficient": 1.30, "nakup_material": 20.00}
wifi_ap	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 10, "cena": 25.00, "nazov": "test3C", "odkaz": "http://odkaztest3c", "pocet": 3, "jednotka": "ks", "dodavatel": "WiFi C", "koeficient": 1.10, "nakup_material": 20.00}
wifi_ap	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 11, "cena": 25.00, "nazov": "test3D", "odkaz": "http://odkaztest3d", "pocet": 4, "jednotka": "ks", "dodavatel": "WiFi D", "koeficient": 1.25, "nakup_material": 20.00}
switche	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 5, "cena": 30.00, "nazov": "test4A", "odkaz": "http://odkaztest4a", "pocet": 1, "jednotka": "ks", "dodavatel": "Switch A", "koeficient": 1.20, "nakup_material": 24.00}
switche	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 6, "cena": 30.00, "nazov": "test4B", "odkaz": "http://odkaztest4b", "pocet": 2, "jednotka": "ks", "dodavatel": "Switch B", "koeficient": 1.30, "nakup_material": 24.00}
switche	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 7, "cena": 30.00, "nazov": "test4C", "odkaz": "http://odkaztest4c", "pocet": 3, "jednotka": "ks", "dodavatel": "Switch C", "koeficient": 1.10, "nakup_material": 24.00}
switche	INSERT	postgres	2025-03-26 22:11:24.019397	\N	{"id": 8, "cena": 30.00, "nazov": "test4D", "odkaz": "http://odkaztest4d", "pocet": 4, "jednotka": "ks", "dodavatel": "Switch D", "koeficient": 1.25, "nakup_material": 24.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 35.00, "nazov": "test5A", "odkaz": "http://odkaztest5a", "pocet": 1, "jednotka": "ks", "dodavatel": "Zaloha A", "koeficient": 1.20, "nakup_material": 28.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 35.00, "nazov": "test5B", "odkaz": "http://odkaztest5b", "pocet": 2, "jednotka": "ks", "dodavatel": "Zaloha B", "koeficient": 1.30, "nakup_material": 28.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 35.00, "nazov": "test5C", "odkaz": "http://odkaztest5c", "pocet": 3, "jednotka": "ks", "dodavatel": "Zaloha C", "koeficient": 1.10, "nakup_material": 28.00}
zalozne_zdroje	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 35.00, "nazov": "test5D", "odkaz": "http://odkaztest5d", "pocet": 4, "jednotka": "ks", "dodavatel": "Zaloha D", "koeficient": 1.25, "nakup_material": 28.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 40.00, "nazov": "test6A", "odkaz": "http://odkaztest6a", "pocet": 1, "jednotka": "ks", "dodavatel": "Batt A", "koeficient": 1.20, "nakup_material": 32.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 40.00, "nazov": "test6B", "odkaz": "http://odkaztest6b", "pocet": 2, "jednotka": "ks", "dodavatel": "Batt B", "koeficient": 1.30, "nakup_material": 32.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 40.00, "nazov": "test6C", "odkaz": "http://odkaztest6c", "pocet": 3, "jednotka": "ks", "dodavatel": "Batt C", "koeficient": 1.10, "nakup_material": 32.00}
zalozne_zdroje_battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 40.00, "nazov": "test6D", "odkaz": "http://odkaztest6d", "pocet": 4, "jednotka": "ks", "dodavatel": "Batt D", "koeficient": 1.25, "nakup_material": 32.00}
battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 45.00, "nazov": "test7A", "odkaz": "http://odkaztest7a", "pocet": 1, "jednotka": "ks", "dodavatel": "BP A", "koeficient": 1.20, "nakup_material": 36.00}
battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 45.00, "nazov": "test7B", "odkaz": "http://odkaztest7b", "pocet": 2, "jednotka": "ks", "dodavatel": "BP B", "koeficient": 1.30, "nakup_material": 36.00}
battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 45.00, "nazov": "test7C", "odkaz": "http://odkaztest7c", "pocet": 3, "jednotka": "ks", "dodavatel": "BP C", "koeficient": 1.10, "nakup_material": 36.00}
battery_packy	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 45.00, "nazov": "test7D", "odkaz": "http://odkaztest7d", "pocet": 4, "jednotka": "ks", "dodavatel": "BP D", "koeficient": 1.25, "nakup_material": 36.00}
kabelaz	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 50.00, "nazov": "test8A", "odkaz": "http://odkaztest8a", "pocet": 1, "jednotka": "ks", "dodavatel": "Kabel A", "koeficient": 1.20, "nakup_material": 40.00}
kabelaz	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 50.00, "nazov": "test8B", "odkaz": "http://odkaztest8b", "pocet": 2, "jednotka": "ks", "dodavatel": "Kabel B", "koeficient": 1.30, "nakup_material": 40.00}
kabelaz	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 50.00, "nazov": "test8C", "odkaz": "http://odkaztest8c", "pocet": 3, "jednotka": "ks", "dodavatel": "Kabel C", "koeficient": 1.10, "nakup_material": 40.00}
kabelaz	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 50.00, "nazov": "test8D", "odkaz": "http://odkaztest8d", "pocet": 4, "jednotka": "ks", "dodavatel": "Kabel D", "koeficient": 1.25, "nakup_material": 40.00}
datove_zasuvky	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 55.00, "nazov": "test9A", "odkaz": "http://odkaztest9a", "pocet": 1, "jednotka": "ks", "dodavatel": "DZ A", "koeficient": 1.20, "nakup_material": 44.00}
datove_zasuvky	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 55.00, "nazov": "test9B", "odkaz": "http://odkaztest9b", "pocet": 2, "jednotka": "ks", "dodavatel": "DZ B", "koeficient": 1.30, "nakup_material": 44.00}
datove_zasuvky	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 55.00, "nazov": "test9C", "odkaz": "http://odkaztest9c", "pocet": 3, "jednotka": "ks", "dodavatel": "DZ C", "koeficient": 1.10, "nakup_material": 44.00}
datove_zasuvky	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 55.00, "nazov": "test9D", "odkaz": "http://odkaztest9d", "pocet": 4, "jednotka": "ks", "dodavatel": "DZ D", "koeficient": 1.25, "nakup_material": 44.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 5, "cena": 60.00, "nazov": "test10A", "odkaz": "http://odkaztest10a", "pocet": 1, "jednotka": "ks", "dodavatel": "PK A", "koeficient": 1.20, "nakup_material": 48.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 6, "cena": 60.00, "nazov": "test10B", "odkaz": "http://odkaztest10b", "pocet": 2, "jednotka": "ks", "dodavatel": "PK B", "koeficient": 1.30, "nakup_material": 48.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 7, "cena": 60.00, "nazov": "test10C", "odkaz": "http://odkaztest10c", "pocet": 3, "jednotka": "ks", "dodavatel": "PK C", "koeficient": 1.10, "nakup_material": 48.00}
podlahove_krabice	INSERT	postgres	2025-03-26 22:12:33.138726	\N	{"id": 8, "cena": 60.00, "nazov": "test10D", "odkaz": "http://odkaztest10d", "pocet": 4, "jednotka": "ks", "dodavatel": "PK D", "koeficient": 1.25, "nakup_material": 48.00}
ustredne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 65.00, "nazov": "test11A", "odkaz": "http://odkaztest11a", "pocet": 1, "jednotka": "ks", "dodavatel": "Ustredna A", "koeficient": 1.20, "nakup_material": 52.00}
ustredne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 65.00, "nazov": "test11B", "odkaz": "http://odkaztest11b", "pocet": 2, "jednotka": "ks", "dodavatel": "Ustredna B", "koeficient": 1.30, "nakup_material": 52.00}
ustredne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 65.00, "nazov": "test11C", "odkaz": "http://odkaztest11c", "pocet": 3, "jednotka": "ks", "dodavatel": "Ustredna C", "koeficient": 1.10, "nakup_material": 52.00}
ustredne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 65.00, "nazov": "test11D", "odkaz": "http://odkaztest11d", "pocet": 4, "jednotka": "ks", "dodavatel": "Ustredna D", "koeficient": 1.25, "nakup_material": 52.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 70.00, "nazov": "test12A", "odkaz": "http://odkaztest12a", "pocet": 1, "jednotka": "ks", "dodavatel": "Radio A", "koeficient": 1.20, "nakup_material": 56.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 70.00, "nazov": "test12B", "odkaz": "http://odkaztest12b", "pocet": 2, "jednotka": "ks", "dodavatel": "Radio B", "koeficient": 1.30, "nakup_material": 56.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 70.00, "nazov": "test12C", "odkaz": "http://odkaztest12c", "pocet": 3, "jednotka": "ks", "dodavatel": "Radio C", "koeficient": 1.10, "nakup_material": 56.00}
radiove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 70.00, "nazov": "test12D", "odkaz": "http://odkaztest12d", "pocet": 4, "jednotka": "ks", "dodavatel": "Radio D", "koeficient": 1.25, "nakup_material": 56.00}
komunikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 75.00, "nazov": "test13A", "odkaz": "http://odkaztest13a", "pocet": 1, "jednotka": "ks", "dodavatel": "Kom A", "koeficient": 1.20, "nakup_material": 60.00}
komunikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 75.00, "nazov": "test13B", "odkaz": "http://odkaztest13b", "pocet": 2, "jednotka": "ks", "dodavatel": "Kom B", "koeficient": 1.30, "nakup_material": 60.00}
komunikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 75.00, "nazov": "test13C", "odkaz": "http://odkaztest13c", "pocet": 3, "jednotka": "ks", "dodavatel": "Kom C", "koeficient": 1.10, "nakup_material": 60.00}
komunikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 75.00, "nazov": "test13D", "odkaz": "http://odkaztest13d", "pocet": 4, "jednotka": "ks", "dodavatel": "Kom D", "koeficient": 1.25, "nakup_material": 60.00}
rozhrania	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 80.00, "nazov": "test14A", "odkaz": "http://odkaztest14a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rozhranie A", "koeficient": 1.20, "nakup_material": 64.00}
rozhrania	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 80.00, "nazov": "test14B", "odkaz": "http://odkaztest14b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rozhranie B", "koeficient": 1.30, "nakup_material": 64.00}
rozhrania	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 80.00, "nazov": "test14C", "odkaz": "http://odkaztest14c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rozhranie C", "koeficient": 1.10, "nakup_material": 64.00}
rozhrania	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 80.00, "nazov": "test14D", "odkaz": "http://odkaztest14d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rozhranie D", "koeficient": 1.25, "nakup_material": 64.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 85.00, "nazov": "test15A", "odkaz": "http://odkaztest15a", "pocet": 1, "jednotka": "ks", "dodavatel": "Pristup A", "koeficient": 1.20, "nakup_material": 68.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 85.00, "nazov": "test15B", "odkaz": "http://odkaztest15b", "pocet": 2, "jednotka": "ks", "dodavatel": "Pristup B", "koeficient": 1.30, "nakup_material": 68.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 85.00, "nazov": "test15C", "odkaz": "http://odkaztest15c", "pocet": 3, "jednotka": "ks", "dodavatel": "Pristup C", "koeficient": 1.10, "nakup_material": 68.00}
pristupove_moduly	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 85.00, "nazov": "test15D", "odkaz": "http://odkaztest15d", "pocet": 4, "jednotka": "ks", "dodavatel": "Pristup D", "koeficient": 1.25, "nakup_material": 68.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 90.00, "nazov": "test16A", "odkaz": "http://odkaztest16a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena In A", "koeficient": 1.20, "nakup_material": 72.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 90.00, "nazov": "test16B", "odkaz": "http://odkaztest16b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena In B", "koeficient": 1.30, "nakup_material": 72.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 90.00, "nazov": "test16C", "odkaz": "http://odkaztest16c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena In C", "koeficient": 1.10, "nakup_material": 72.00}
sireny_vnutorne	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 90.00, "nazov": "test16D", "odkaz": "http://odkaztest16d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena In D", "koeficient": 1.25, "nakup_material": 72.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 95.00, "nazov": "test17A", "odkaz": "http://odkaztest17a", "pocet": 1, "jednotka": "ks", "dodavatel": "Sirena Out A", "koeficient": 1.20, "nakup_material": 76.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 95.00, "nazov": "test17B", "odkaz": "http://odkaztest17b", "pocet": 2, "jednotka": "ks", "dodavatel": "Sirena Out B", "koeficient": 1.30, "nakup_material": 76.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 95.00, "nazov": "test17C", "odkaz": "http://odkaztest17c", "pocet": 3, "jednotka": "ks", "dodavatel": "Sirena Out C", "koeficient": 1.10, "nakup_material": 76.00}
sireny_vonkajsie	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 95.00, "nazov": "test17D", "odkaz": "http://odkaztest17d", "pocet": 4, "jednotka": "ks", "dodavatel": "Sirena Out D", "koeficient": 1.25, "nakup_material": 76.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 100.00, "nazov": "test18A", "odkaz": "http://odkaztest18a", "pocet": 1, "jednotka": "ks", "dodavatel": "Detektor A", "koeficient": 1.20, "nakup_material": 80.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 100.00, "nazov": "test18B", "odkaz": "http://odkaztest18b", "pocet": 2, "jednotka": "ks", "dodavatel": "Detektor B", "koeficient": 1.30, "nakup_material": 80.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 100.00, "nazov": "test18C", "odkaz": "http://odkaztest18c", "pocet": 3, "jednotka": "ks", "dodavatel": "Detektor C", "koeficient": 1.10, "nakup_material": 80.00}
pohybove_detektory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 100.00, "nazov": "test18D", "odkaz": "http://odkaztest18d", "pocet": 4, "jednotka": "ks", "dodavatel": "Detektor D", "koeficient": 1.25, "nakup_material": 80.00}
rele	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 5, "cena": 105.00, "nazov": "test19A", "odkaz": "http://odkaztest19a", "pocet": 1, "jednotka": "ks", "dodavatel": "Rele A", "koeficient": 1.20, "nakup_material": 84.00}
rele	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 105.00, "nazov": "test19B", "odkaz": "http://odkaztest19b", "pocet": 2, "jednotka": "ks", "dodavatel": "Rele B", "koeficient": 1.30, "nakup_material": 84.00}
rele	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 105.00, "nazov": "test19C", "odkaz": "http://odkaztest19c", "pocet": 3, "jednotka": "ks", "dodavatel": "Rele C", "koeficient": 1.10, "nakup_material": 84.00}
rele	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 105.00, "nazov": "test19D", "odkaz": "http://odkaztest19d", "pocet": 4, "jednotka": "ks", "dodavatel": "Rele D", "koeficient": 1.25, "nakup_material": 84.00}
indikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 6, "cena": 110.00, "nazov": "test20A", "odkaz": "http://odkaztest20a", "pocet": 1, "jednotka": "ks", "dodavatel": "Indikator A", "koeficient": 1.20, "nakup_material": 88.00}
indikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 7, "cena": 110.00, "nazov": "test20B", "odkaz": "http://odkaztest20b", "pocet": 2, "jednotka": "ks", "dodavatel": "Indikator B", "koeficient": 1.30, "nakup_material": 88.00}
indikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 8, "cena": 110.00, "nazov": "test20C", "odkaz": "http://odkaztest20c", "pocet": 3, "jednotka": "ks", "dodavatel": "Indikator C", "koeficient": 1.10, "nakup_material": 88.00}
indikatory	INSERT	postgres	2025-03-26 22:13:36.148838	\N	{"id": 9, "cena": 110.00, "nazov": "test20D", "odkaz": "http://odkaztest20d", "pocet": 4, "jednotka": "ks", "dodavatel": "Indikator D", "koeficient": 1.25, "nakup_material": 88.00}
\.


--
-- TOC entry 5082 (class 0 OID 16444)
-- Dependencies: 230
-- Data for Name: battery_packy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.battery_packy (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test7A	ks	1	BP A	http://odkaztest7a	1.20	36.00
6	test7B	ks	2	BP B	http://odkaztest7b	1.30	36.00
7	test7C	ks	3	BP C	http://odkaztest7c	1.10	36.00
8	test7D	ks	4	BP D	http://odkaztest7d	1.25	36.00
\.


--
-- TOC entry 5086 (class 0 OID 16462)
-- Dependencies: 234
-- Data for Name: datove_zasuvky; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.datove_zasuvky (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test9A	ks	1	DZ A	http://odkaztest9a	1.20	44.00
6	test9B	ks	2	DZ B	http://odkaztest9b	1.30	44.00
7	test9C	ks	3	DZ C	http://odkaztest9c	1.10	44.00
8	test9D	ks	4	DZ D	http://odkaztest9d	1.25	44.00
\.


--
-- TOC entry 5108 (class 0 OID 16561)
-- Dependencies: 256
-- Data for Name: indikatory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.indikatory (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
6	test20A	ks	1	Indikator A	http://odkaztest20a	1.20	88.00
7	test20B	ks	2	Indikator B	http://odkaztest20b	1.30	88.00
8	test20C	ks	3	Indikator C	http://odkaztest20c	1.10	88.00
9	test20D	ks	4	Indikator D	http://odkaztest20d	1.25	88.00
\.


--
-- TOC entry 5084 (class 0 OID 16453)
-- Dependencies: 232
-- Data for Name: kabelaz; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.kabelaz (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test8A	ks	1	Kabel A	http://odkaztest8a	1.20	40.00
6	test8B	ks	2	Kabel B	http://odkaztest8b	1.30	40.00
7	test8C	ks	3	Kabel C	http://odkaztest8c	1.10	40.00
8	test8D	ks	4	Kabel D	http://odkaztest8d	1.25	40.00
\.


--
-- TOC entry 5094 (class 0 OID 16498)
-- Dependencies: 242
-- Data for Name: komunikatory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.komunikatory (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test13A	ks	1	Kom A	http://odkaztest13a	1.20	60.00
6	test13B	ks	2	Kom B	http://odkaztest13b	1.30	60.00
7	test13C	ks	3	Kom C	http://odkaztest13c	1.10	60.00
8	test13D	ks	4	Kom D	http://odkaztest13d	1.25	60.00
\.


--
-- TOC entry 5088 (class 0 OID 16471)
-- Dependencies: 236
-- Data for Name: podlahove_krabice; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.podlahove_krabice (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test10A	ks	1	PK A	http://odkaztest10a	1.20	48.00
6	test10B	ks	2	PK B	http://odkaztest10b	1.30	48.00
7	test10C	ks	3	PK C	http://odkaztest10c	1.10	48.00
8	test10D	ks	4	PK D	http://odkaztest10d	1.25	48.00
\.


--
-- TOC entry 5104 (class 0 OID 16543)
-- Dependencies: 252
-- Data for Name: pohybove_detektory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pohybove_detektory (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test18A	ks	1	Detektor A	http://odkaztest18a	1.20	80.00
6	test18B	ks	2	Detektor B	http://odkaztest18b	1.30	80.00
7	test18C	ks	3	Detektor C	http://odkaztest18c	1.10	80.00
8	test18D	ks	4	Detektor D	http://odkaztest18d	1.25	80.00
\.


--
-- TOC entry 5098 (class 0 OID 16516)
-- Dependencies: 246
-- Data for Name: pristupove_moduly; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pristupove_moduly (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test15A	ks	1	Pristup A	http://odkaztest15a	1.20	68.00
6	test15B	ks	2	Pristup B	http://odkaztest15b	1.30	68.00
7	test15C	ks	3	Pristup C	http://odkaztest15c	1.10	68.00
8	test15D	ks	4	Pristup D	http://odkaztest15d	1.25	68.00
\.


--
-- TOC entry 5092 (class 0 OID 16489)
-- Dependencies: 240
-- Data for Name: radiove_moduly; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.radiove_moduly (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test12A	ks	1	Radio A	http://odkaztest12a	1.20	56.00
6	test12B	ks	2	Radio B	http://odkaztest12b	1.30	56.00
7	test12C	ks	3	Radio C	http://odkaztest12c	1.10	56.00
8	test12D	ks	4	Radio D	http://odkaztest12d	1.25	56.00
\.


--
-- TOC entry 5106 (class 0 OID 16552)
-- Dependencies: 254
-- Data for Name: rele; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rele (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test19A	ks	1	Rele A	http://odkaztest19a	1.20	84.00
6	test19B	ks	2	Rele B	http://odkaztest19b	1.30	84.00
7	test19C	ks	3	Rele C	http://odkaztest19c	1.10	84.00
8	test19D	ks	4	Rele D	http://odkaztest19d	1.25	84.00
\.


--
-- TOC entry 5096 (class 0 OID 16507)
-- Dependencies: 244
-- Data for Name: rozhrania; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rozhrania (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test14A	ks	1	Rozhranie A	http://odkaztest14a	1.20	64.00
6	test14B	ks	2	Rozhranie B	http://odkaztest14b	1.30	64.00
7	test14C	ks	3	Rozhranie C	http://odkaztest14c	1.10	64.00
8	test14D	ks	4	Rozhranie D	http://odkaztest14d	1.25	64.00
\.


--
-- TOC entry 5070 (class 0 OID 16390)
-- Dependencies: 218
-- Data for Name: rozvadzace; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rozvadzace (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
17	test1A	ks	1	Dodavatel A	http://odkaztest1a	1.20	12.00
18	test1B	ks	2	Dodavatel B	http://odkaztest1b	1.30	12.00
19	test1C	ks	3	Dodavatel C	http://odkaztest1c	1.10	12.00
20	test1D	ks	4	Dodavatel D	http://odkaztest1d	1.25	12.00
\.


--
-- TOC entry 5100 (class 0 OID 16525)
-- Dependencies: 248
-- Data for Name: sireny_vnutorne; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sireny_vnutorne (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test16A	ks	1	Sirena In A	http://odkaztest16a	1.20	72.00
6	test16B	ks	2	Sirena In B	http://odkaztest16b	1.30	72.00
7	test16C	ks	3	Sirena In C	http://odkaztest16c	1.10	72.00
8	test16D	ks	4	Sirena In D	http://odkaztest16d	1.25	72.00
\.


--
-- TOC entry 5102 (class 0 OID 16534)
-- Dependencies: 250
-- Data for Name: sireny_vonkajsie; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sireny_vonkajsie (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test17A	ks	1	Sirena Out A	http://odkaztest17a	1.20	76.00
6	test17B	ks	2	Sirena Out B	http://odkaztest17b	1.30	76.00
7	test17C	ks	3	Sirena Out C	http://odkaztest17c	1.10	76.00
8	test17D	ks	4	Sirena Out D	http://odkaztest17d	1.25	76.00
\.


--
-- TOC entry 5076 (class 0 OID 16417)
-- Dependencies: 224
-- Data for Name: switche; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.switche (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test4A	ks	1	Switch A	http://odkaztest4a	1.20	24.00
6	test4B	ks	2	Switch B	http://odkaztest4b	1.30	24.00
7	test4C	ks	3	Switch C	http://odkaztest4c	1.10	24.00
8	test4D	ks	4	Switch D	http://odkaztest4d	1.25	24.00
\.


--
-- TOC entry 5090 (class 0 OID 16480)
-- Dependencies: 238
-- Data for Name: ustredne; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ustredne (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test11A	ks	1	Ustredna A	http://odkaztest11a	1.20	52.00
6	test11B	ks	2	Ustredna B	http://odkaztest11b	1.30	52.00
7	test11C	ks	3	Ustredna C	http://odkaztest11c	1.10	52.00
8	test11D	ks	4	Ustredna D	http://odkaztest11d	1.25	52.00
\.


--
-- TOC entry 5072 (class 0 OID 16399)
-- Dependencies: 220
-- Data for Name: vybava_rozvadzacov; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vybava_rozvadzacov (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test2A	ks	1	Dodavatel A	http://odkaztest2a	1.20	16.00
6	test2B	ks	2	Dodavatel B	http://odkaztest2b	1.30	16.00
7	test2C	ks	3	Dodavatel C	http://odkaztest2c	1.10	16.00
8	test2D	ks	4	Dodavatel D	http://odkaztest2d	1.25	16.00
\.


--
-- TOC entry 5074 (class 0 OID 16408)
-- Dependencies: 222
-- Data for Name: wifi_ap; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wifi_ap (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
8	test3A	ks	1	WiFi A	http://odkaztest3a	1.20	20.00
9	test3B	ks	2	WiFi B	http://odkaztest3b	1.30	20.00
10	test3C	ks	3	WiFi C	http://odkaztest3c	1.10	20.00
11	test3D	ks	4	WiFi D	http://odkaztest3d	1.25	20.00
\.


--
-- TOC entry 5078 (class 0 OID 16426)
-- Dependencies: 226
-- Data for Name: zalozne_zdroje; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zalozne_zdroje (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test5A	ks	1	Zaloha A	http://odkaztest5a	1.20	28.00
6	test5B	ks	2	Zaloha B	http://odkaztest5b	1.30	28.00
7	test5C	ks	3	Zaloha C	http://odkaztest5c	1.10	28.00
8	test5D	ks	4	Zaloha D	http://odkaztest5d	1.25	28.00
\.


--
-- TOC entry 5080 (class 0 OID 16435)
-- Dependencies: 228
-- Data for Name: zalozne_zdroje_battery_packy; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zalozne_zdroje_battery_packy (id, nazov, jednotka, pocet, dodavatel, odkaz, koeficient, nakup_material) FROM stdin;
5	test6A	ks	1	Batt A	http://odkaztest6a	1.20	32.00
6	test6B	ks	2	Batt B	http://odkaztest6b	1.30	32.00
7	test6C	ks	3	Batt C	http://odkaztest6c	1.10	32.00
8	test6D	ks	4	Batt D	http://odkaztest6d	1.25	32.00
\.


--
-- TOC entry 5177 (class 0 OID 0)
-- Dependencies: 229
-- Name: battery_packy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.battery_packy_id_seq', 8, true);


--
-- TOC entry 5178 (class 0 OID 0)
-- Dependencies: 233
-- Name: datove_zasuvky_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.datove_zasuvky_id_seq', 8, true);


--
-- TOC entry 5179 (class 0 OID 0)
-- Dependencies: 255
-- Name: indikatory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.indikatory_id_seq', 9, true);


--
-- TOC entry 5180 (class 0 OID 0)
-- Dependencies: 231
-- Name: kabelaz_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.kabelaz_id_seq', 8, true);


--
-- TOC entry 5181 (class 0 OID 0)
-- Dependencies: 241
-- Name: komunikatory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.komunikatory_id_seq', 8, true);


--
-- TOC entry 5182 (class 0 OID 0)
-- Dependencies: 235
-- Name: podlahove_krabice_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.podlahove_krabice_id_seq', 8, true);


--
-- TOC entry 5183 (class 0 OID 0)
-- Dependencies: 251
-- Name: pohybove_detektory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pohybove_detektory_id_seq', 8, true);


--
-- TOC entry 5184 (class 0 OID 0)
-- Dependencies: 245
-- Name: pristupove_moduly_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pristupove_moduly_id_seq', 8, true);


--
-- TOC entry 5185 (class 0 OID 0)
-- Dependencies: 239
-- Name: radiove_moduly_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.radiove_moduly_id_seq', 8, true);


--
-- TOC entry 5186 (class 0 OID 0)
-- Dependencies: 253
-- Name: rele_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rele_id_seq', 8, true);


--
-- TOC entry 5187 (class 0 OID 0)
-- Dependencies: 243
-- Name: rozhrania_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rozhrania_id_seq', 8, true);


--
-- TOC entry 5188 (class 0 OID 0)
-- Dependencies: 217
-- Name: rozvadzace_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rozvadzace_id_seq', 20, true);


--
-- TOC entry 5189 (class 0 OID 0)
-- Dependencies: 247
-- Name: sireny_vnutorne_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sireny_vnutorne_id_seq', 8, true);


--
-- TOC entry 5190 (class 0 OID 0)
-- Dependencies: 249
-- Name: sireny_vonkajsie_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sireny_vonkajsie_id_seq', 8, true);


--
-- TOC entry 5191 (class 0 OID 0)
-- Dependencies: 223
-- Name: switche_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.switche_id_seq', 8, true);


--
-- TOC entry 5192 (class 0 OID 0)
-- Dependencies: 237
-- Name: ustredne_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ustredne_id_seq', 8, true);


--
-- TOC entry 5193 (class 0 OID 0)
-- Dependencies: 219
-- Name: vybava_rozvadzacov_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vybava_rozvadzacov_id_seq', 8, true);


--
-- TOC entry 5194 (class 0 OID 0)
-- Dependencies: 221
-- Name: wifi_ap_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wifi_ap_id_seq', 11, true);


--
-- TOC entry 5195 (class 0 OID 0)
-- Dependencies: 227
-- Name: zalozne_zdroje_battery_packy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zalozne_zdroje_battery_packy_id_seq', 8, true);


--
-- TOC entry 5196 (class 0 OID 0)
-- Dependencies: 225
-- Name: zalozne_zdroje_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zalozne_zdroje_id_seq', 8, true);


--
-- TOC entry 4877 (class 2606 OID 16451)
-- Name: battery_packy battery_packy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battery_packy
    ADD CONSTRAINT battery_packy_pkey PRIMARY KEY (id);


--
-- TOC entry 4881 (class 2606 OID 16469)
-- Name: datove_zasuvky datove_zasuvky_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.datove_zasuvky
    ADD CONSTRAINT datove_zasuvky_pkey PRIMARY KEY (id);


--
-- TOC entry 4903 (class 2606 OID 16568)
-- Name: indikatory indikatory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.indikatory
    ADD CONSTRAINT indikatory_pkey PRIMARY KEY (id);


--
-- TOC entry 4879 (class 2606 OID 16460)
-- Name: kabelaz kabelaz_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kabelaz
    ADD CONSTRAINT kabelaz_pkey PRIMARY KEY (id);


--
-- TOC entry 4889 (class 2606 OID 16505)
-- Name: komunikatory komunikatory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.komunikatory
    ADD CONSTRAINT komunikatory_pkey PRIMARY KEY (id);


--
-- TOC entry 4883 (class 2606 OID 16478)
-- Name: podlahove_krabice podlahove_krabice_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.podlahove_krabice
    ADD CONSTRAINT podlahove_krabice_pkey PRIMARY KEY (id);


--
-- TOC entry 4899 (class 2606 OID 16550)
-- Name: pohybove_detektory pohybove_detektory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pohybove_detektory
    ADD CONSTRAINT pohybove_detektory_pkey PRIMARY KEY (id);


--
-- TOC entry 4893 (class 2606 OID 16523)
-- Name: pristupove_moduly pristupove_moduly_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pristupove_moduly
    ADD CONSTRAINT pristupove_moduly_pkey PRIMARY KEY (id);


--
-- TOC entry 4887 (class 2606 OID 16496)
-- Name: radiove_moduly radiove_moduly_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiove_moduly
    ADD CONSTRAINT radiove_moduly_pkey PRIMARY KEY (id);


--
-- TOC entry 4901 (class 2606 OID 16559)
-- Name: rele rele_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rele
    ADD CONSTRAINT rele_pkey PRIMARY KEY (id);


--
-- TOC entry 4891 (class 2606 OID 16514)
-- Name: rozhrania rozhrania_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rozhrania
    ADD CONSTRAINT rozhrania_pkey PRIMARY KEY (id);


--
-- TOC entry 4865 (class 2606 OID 16397)
-- Name: rozvadzace rozvadzace_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rozvadzace
    ADD CONSTRAINT rozvadzace_pkey PRIMARY KEY (id);


--
-- TOC entry 4895 (class 2606 OID 16532)
-- Name: sireny_vnutorne sireny_vnutorne_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sireny_vnutorne
    ADD CONSTRAINT sireny_vnutorne_pkey PRIMARY KEY (id);


--
-- TOC entry 4897 (class 2606 OID 16541)
-- Name: sireny_vonkajsie sireny_vonkajsie_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sireny_vonkajsie
    ADD CONSTRAINT sireny_vonkajsie_pkey PRIMARY KEY (id);


--
-- TOC entry 4871 (class 2606 OID 16424)
-- Name: switche switche_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.switche
    ADD CONSTRAINT switche_pkey PRIMARY KEY (id);


--
-- TOC entry 4885 (class 2606 OID 16487)
-- Name: ustredne ustredne_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ustredne
    ADD CONSTRAINT ustredne_pkey PRIMARY KEY (id);


--
-- TOC entry 4867 (class 2606 OID 16406)
-- Name: vybava_rozvadzacov vybava_rozvadzacov_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vybava_rozvadzacov
    ADD CONSTRAINT vybava_rozvadzacov_pkey PRIMARY KEY (id);


--
-- TOC entry 4869 (class 2606 OID 16415)
-- Name: wifi_ap wifi_ap_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wifi_ap
    ADD CONSTRAINT wifi_ap_pkey PRIMARY KEY (id);


--
-- TOC entry 4875 (class 2606 OID 16442)
-- Name: zalozne_zdroje_battery_packy zalozne_zdroje_battery_packy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zalozne_zdroje_battery_packy
    ADD CONSTRAINT zalozne_zdroje_battery_packy_pkey PRIMARY KEY (id);


--
-- TOC entry 4873 (class 2606 OID 16433)
-- Name: zalozne_zdroje zalozne_zdroje_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zalozne_zdroje
    ADD CONSTRAINT zalozne_zdroje_pkey PRIMARY KEY (id);


--
-- TOC entry 4910 (class 2620 OID 16609)
-- Name: battery_packy trg_audit_battery_packy; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_battery_packy AFTER INSERT OR DELETE OR UPDATE ON public.battery_packy FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4912 (class 2620 OID 16610)
-- Name: datove_zasuvky trg_audit_datove_zasuvky; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_datove_zasuvky AFTER INSERT OR DELETE OR UPDATE ON public.datove_zasuvky FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4923 (class 2620 OID 16612)
-- Name: indikatory trg_audit_indikatory; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_indikatory AFTER INSERT OR DELETE OR UPDATE ON public.indikatory FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4911 (class 2620 OID 16596)
-- Name: kabelaz trg_audit_kabelaz; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_kabelaz AFTER INSERT OR DELETE OR UPDATE ON public.kabelaz FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4916 (class 2620 OID 16598)
-- Name: komunikatory trg_audit_komunikatory; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_komunikatory AFTER INSERT OR DELETE OR UPDATE ON public.komunikatory FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4913 (class 2620 OID 16611)
-- Name: podlahove_krabice trg_audit_podlahove_krabice; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_podlahove_krabice AFTER INSERT OR DELETE OR UPDATE ON public.podlahove_krabice FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4921 (class 2620 OID 16604)
-- Name: pohybove_detektory trg_audit_pohybove_detektory; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_pohybove_detektory AFTER INSERT OR DELETE OR UPDATE ON public.pohybove_detektory FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4918 (class 2620 OID 16601)
-- Name: pristupove_moduly trg_audit_pristupove_moduly; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_pristupove_moduly AFTER INSERT OR DELETE OR UPDATE ON public.pristupove_moduly FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4915 (class 2620 OID 16597)
-- Name: radiove_moduly trg_audit_radiove_moduly; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_radiove_moduly AFTER INSERT OR DELETE OR UPDATE ON public.radiove_moduly FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4922 (class 2620 OID 16605)
-- Name: rele trg_audit_rele; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_rele AFTER INSERT OR DELETE OR UPDATE ON public.rele FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4917 (class 2620 OID 16599)
-- Name: rozhrania trg_audit_rozhrania; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_rozhrania AFTER INSERT OR DELETE OR UPDATE ON public.rozhrania FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4904 (class 2620 OID 16593)
-- Name: rozvadzace trg_audit_rozvadzace; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_rozvadzace AFTER INSERT OR DELETE OR UPDATE ON public.rozvadzace FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4919 (class 2620 OID 16602)
-- Name: sireny_vnutorne trg_audit_sireny_vnutorne; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_sireny_vnutorne AFTER INSERT OR DELETE OR UPDATE ON public.sireny_vnutorne FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4920 (class 2620 OID 16603)
-- Name: sireny_vonkajsie trg_audit_sireny_vonkajsie; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_sireny_vonkajsie AFTER INSERT OR DELETE OR UPDATE ON public.sireny_vonkajsie FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4907 (class 2620 OID 16606)
-- Name: switche trg_audit_switche; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_switche AFTER INSERT OR DELETE OR UPDATE ON public.switche FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4914 (class 2620 OID 16600)
-- Name: ustredne trg_audit_ustredne; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_ustredne AFTER INSERT OR DELETE OR UPDATE ON public.ustredne FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4905 (class 2620 OID 16594)
-- Name: vybava_rozvadzacov trg_audit_vybava_rozvadzacov; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_vybava_rozvadzacov AFTER INSERT OR DELETE OR UPDATE ON public.vybava_rozvadzacov FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4906 (class 2620 OID 16595)
-- Name: wifi_ap trg_audit_wifi_ap; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_wifi_ap AFTER INSERT OR DELETE OR UPDATE ON public.wifi_ap FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4908 (class 2620 OID 16607)
-- Name: zalozne_zdroje trg_audit_zalozne_zdroje; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_zalozne_zdroje AFTER INSERT OR DELETE OR UPDATE ON public.zalozne_zdroje FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 4909 (class 2620 OID 16608)
-- Name: zalozne_zdroje_battery_packy trg_audit_zalozne_zdroje_battery_packy; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_zalozne_zdroje_battery_packy AFTER INSERT OR DELETE OR UPDATE ON public.zalozne_zdroje_battery_packy FOR EACH ROW EXECUTE FUNCTION public.log_audit();


--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT USAGE ON SCHEMA public TO user1;
GRANT USAGE ON SCHEMA public TO user2;
GRANT USAGE ON SCHEMA public TO user3;
GRANT USAGE ON SCHEMA public TO user4;
GRANT USAGE ON SCHEMA public TO user5;
GRANT USAGE ON SCHEMA public TO user6;
GRANT USAGE ON SCHEMA public TO user7;
GRANT USAGE ON SCHEMA public TO user8;
GRANT USAGE ON SCHEMA public TO app_user;


--
-- TOC entry 5116 (class 0 OID 0)
-- Dependencies: 257
-- Name: TABLE audit_log; Type: ACL; Schema: public; Owner: admin_user
--

GRANT INSERT ON TABLE public.audit_log TO app_user;


--
-- TOC entry 5117 (class 0 OID 0)
-- Dependencies: 230
-- Name: TABLE battery_packy; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.battery_packy TO app_user;


--
-- TOC entry 5119 (class 0 OID 0)
-- Dependencies: 229
-- Name: SEQUENCE battery_packy_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.battery_packy_id_seq TO PUBLIC;


--
-- TOC entry 5120 (class 0 OID 0)
-- Dependencies: 234
-- Name: TABLE datove_zasuvky; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.datove_zasuvky TO app_user;


--
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 233
-- Name: SEQUENCE datove_zasuvky_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.datove_zasuvky_id_seq TO PUBLIC;


--
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 256
-- Name: TABLE indikatory; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.indikatory TO app_user;


--
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 255
-- Name: SEQUENCE indikatory_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.indikatory_id_seq TO PUBLIC;


--
-- TOC entry 5126 (class 0 OID 0)
-- Dependencies: 232
-- Name: TABLE kabelaz; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.kabelaz TO app_user;


--
-- TOC entry 5128 (class 0 OID 0)
-- Dependencies: 231
-- Name: SEQUENCE kabelaz_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.kabelaz_id_seq TO PUBLIC;


--
-- TOC entry 5129 (class 0 OID 0)
-- Dependencies: 242
-- Name: TABLE komunikatory; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.komunikatory TO app_user;


--
-- TOC entry 5131 (class 0 OID 0)
-- Dependencies: 241
-- Name: SEQUENCE komunikatory_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.komunikatory_id_seq TO PUBLIC;


--
-- TOC entry 5132 (class 0 OID 0)
-- Dependencies: 236
-- Name: TABLE podlahove_krabice; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.podlahove_krabice TO app_user;


--
-- TOC entry 5134 (class 0 OID 0)
-- Dependencies: 235
-- Name: SEQUENCE podlahove_krabice_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.podlahove_krabice_id_seq TO PUBLIC;


--
-- TOC entry 5135 (class 0 OID 0)
-- Dependencies: 252
-- Name: TABLE pohybove_detektory; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pohybove_detektory TO app_user;


--
-- TOC entry 5137 (class 0 OID 0)
-- Dependencies: 251
-- Name: SEQUENCE pohybove_detektory_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.pohybove_detektory_id_seq TO PUBLIC;


--
-- TOC entry 5138 (class 0 OID 0)
-- Dependencies: 246
-- Name: TABLE pristupove_moduly; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pristupove_moduly TO app_user;


--
-- TOC entry 5140 (class 0 OID 0)
-- Dependencies: 245
-- Name: SEQUENCE pristupove_moduly_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.pristupove_moduly_id_seq TO PUBLIC;


--
-- TOC entry 5141 (class 0 OID 0)
-- Dependencies: 240
-- Name: TABLE radiove_moduly; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.radiove_moduly TO app_user;


--
-- TOC entry 5143 (class 0 OID 0)
-- Dependencies: 239
-- Name: SEQUENCE radiove_moduly_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.radiove_moduly_id_seq TO PUBLIC;


--
-- TOC entry 5144 (class 0 OID 0)
-- Dependencies: 254
-- Name: TABLE rele; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rele TO app_user;


--
-- TOC entry 5146 (class 0 OID 0)
-- Dependencies: 253
-- Name: SEQUENCE rele_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.rele_id_seq TO PUBLIC;


--
-- TOC entry 5147 (class 0 OID 0)
-- Dependencies: 244
-- Name: TABLE rozhrania; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozhrania TO app_user;


--
-- TOC entry 5149 (class 0 OID 0)
-- Dependencies: 243
-- Name: SEQUENCE rozhrania_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.rozhrania_id_seq TO PUBLIC;


--
-- TOC entry 5150 (class 0 OID 0)
-- Dependencies: 218
-- Name: TABLE rozvadzace; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.rozvadzace TO app_user;


--
-- TOC entry 5152 (class 0 OID 0)
-- Dependencies: 217
-- Name: SEQUENCE rozvadzace_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.rozvadzace_id_seq TO PUBLIC;


--
-- TOC entry 5153 (class 0 OID 0)
-- Dependencies: 248
-- Name: TABLE sireny_vnutorne; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vnutorne TO app_user;


--
-- TOC entry 5155 (class 0 OID 0)
-- Dependencies: 247
-- Name: SEQUENCE sireny_vnutorne_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.sireny_vnutorne_id_seq TO PUBLIC;


--
-- TOC entry 5156 (class 0 OID 0)
-- Dependencies: 250
-- Name: TABLE sireny_vonkajsie; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sireny_vonkajsie TO app_user;


--
-- TOC entry 5158 (class 0 OID 0)
-- Dependencies: 249
-- Name: SEQUENCE sireny_vonkajsie_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.sireny_vonkajsie_id_seq TO PUBLIC;


--
-- TOC entry 5159 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE switche; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.switche TO app_user;


--
-- TOC entry 5161 (class 0 OID 0)
-- Dependencies: 223
-- Name: SEQUENCE switche_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.switche_id_seq TO PUBLIC;


--
-- TOC entry 5162 (class 0 OID 0)
-- Dependencies: 238
-- Name: TABLE ustredne; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ustredne TO app_user;


--
-- TOC entry 5164 (class 0 OID 0)
-- Dependencies: 237
-- Name: SEQUENCE ustredne_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.ustredne_id_seq TO PUBLIC;


--
-- TOC entry 5165 (class 0 OID 0)
-- Dependencies: 220
-- Name: TABLE vybava_rozvadzacov; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.vybava_rozvadzacov TO app_user;


--
-- TOC entry 5167 (class 0 OID 0)
-- Dependencies: 219
-- Name: SEQUENCE vybava_rozvadzacov_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.vybava_rozvadzacov_id_seq TO PUBLIC;


--
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 222
-- Name: TABLE wifi_ap; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.wifi_ap TO app_user;


--
-- TOC entry 5170 (class 0 OID 0)
-- Dependencies: 221
-- Name: SEQUENCE wifi_ap_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.wifi_ap_id_seq TO PUBLIC;


--
-- TOC entry 5171 (class 0 OID 0)
-- Dependencies: 226
-- Name: TABLE zalozne_zdroje; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje TO app_user;


--
-- TOC entry 5172 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE zalozne_zdroje_battery_packy; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user1;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user2;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user3;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user4;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user5;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user6;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user7;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO user8;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.zalozne_zdroje_battery_packy TO app_user;


--
-- TOC entry 5174 (class 0 OID 0)
-- Dependencies: 227
-- Name: SEQUENCE zalozne_zdroje_battery_packy_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.zalozne_zdroje_battery_packy_id_seq TO PUBLIC;


--
-- TOC entry 5176 (class 0 OID 0)
-- Dependencies: 225
-- Name: SEQUENCE zalozne_zdroje_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.zalozne_zdroje_id_seq TO PUBLIC;


--
-- TOC entry 2144 (class 826 OID 16585)
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user1;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user2;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user3;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user4;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user5;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user6;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user7;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO user8;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO app_user;


-- Completed on 2025-03-28 11:53:41

--
-- PostgreSQL database dump complete
--

