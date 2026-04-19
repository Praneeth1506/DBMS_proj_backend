--
-- PostgreSQL database dump
--

\restrict dIfMbyfHqenEi4LAyfovhjxluOCmkoHDyE0jveEUpM9fniTR7fd9OCINOUCAd7g

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: calendarevent; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.calendarevent (
    eventid integer NOT NULL,
    userid integer,
    relatedpersonid integer,
    eventtitle character varying(100),
    eventdatetime timestamp without time zone,
    remindertime timestamp without time zone
);


ALTER TABLE public.calendarevent OWNER TO postgres;

--
-- Name: calendarevent_eventid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.calendarevent_eventid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.calendarevent_eventid_seq OWNER TO postgres;

--
-- Name: calendarevent_eventid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.calendarevent_eventid_seq OWNED BY public.calendarevent.eventid;


--
-- Name: caregiver; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.caregiver (
    caregiverid integer NOT NULL,
    name character varying(100),
    relationshiptouser character varying(50),
    accesslevel character varying(20)
);


ALTER TABLE public.caregiver OWNER TO postgres;

--
-- Name: caregiver_caregiverid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.caregiver_caregiverid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.caregiver_caregiverid_seq OWNER TO postgres;

--
-- Name: caregiver_caregiverid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.caregiver_caregiverid_seq OWNED BY public.caregiver.caregiverid;


--
-- Name: conversation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.conversation (
    interactionid integer NOT NULL,
    userid integer,
    personid integer,
    interactiondatetime timestamp without time zone,
    location character varying(100),
    conversation text,
    summarytext text,
    emotiondetected character varying(50)
);


ALTER TABLE public.conversation OWNER TO postgres;

--
-- Name: conversation_interactionid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.conversation_interactionid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conversation_interactionid_seq OWNER TO postgres;

--
-- Name: conversation_interactionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.conversation_interactionid_seq OWNED BY public.conversation.interactionid;


--
-- Name: emotionrecord; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.emotionrecord (
    emotionid integer NOT NULL,
    interactionid integer,
    emotiontype character varying(50),
    confidencelevel numeric(5,2)
);


ALTER TABLE public.emotionrecord OWNER TO postgres;

--
-- Name: emotionrecord_emotionid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.emotionrecord_emotionid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.emotionrecord_emotionid_seq OWNER TO postgres;

--
-- Name: emotionrecord_emotionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.emotionrecord_emotionid_seq OWNED BY public.emotionrecord.emotionid;


--
-- Name: faceencoding; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.faceencoding (
    faceencodingid integer NOT NULL,
    personid integer,
    encodingdata text,
    confidencescore numeric(5,2),
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.faceencoding OWNER TO postgres;

--
-- Name: faceencoding_faceencodingid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.faceencoding_faceencodingid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.faceencoding_faceencodingid_seq OWNER TO postgres;

--
-- Name: faceencoding_faceencodingid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.faceencoding_faceencodingid_seq OWNED BY public.faceencoding.faceencodingid;


--
-- Name: knownperson; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knownperson (
    personid integer NOT NULL,
    name character varying(100),
    relationshiptype character varying(50),
    prioritylevel integer,
    notes text
);


ALTER TABLE public.knownperson OWNER TO postgres;

--
-- Name: knownperson_personid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.knownperson_personid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.knownperson_personid_seq OWNER TO postgres;

--
-- Name: knownperson_personid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.knownperson_personid_seq OWNED BY public.knownperson.personid;


--
-- Name: note; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.note (
    noteid integer NOT NULL,
    interactionid integer,
    content text,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    importancelevel integer
);


ALTER TABLE public.note OWNER TO postgres;

--
-- Name: note_noteid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.note_noteid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.note_noteid_seq OWNER TO postgres;

--
-- Name: note_noteid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.note_noteid_seq OWNED BY public.note.noteid;


--
-- Name: usercaregiver; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usercaregiver (
    userid integer NOT NULL,
    caregiverid integer NOT NULL
);


ALTER TABLE public.usercaregiver OWNER TO postgres;

--
-- Name: userknownperson; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userknownperson (
    userid integer NOT NULL,
    personid integer NOT NULL
);


ALTER TABLE public.userknownperson OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    userid integer NOT NULL,
    name character varying(100),
    age integer,
    medicalcondition text,
    emergencycontact character varying(20),
    email character varying(150) UNIQUE,
    google_token_json JSON,
    createdat timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_userid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_userid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_userid_seq OWNER TO postgres;

--
-- Name: users_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_userid_seq OWNED BY public.users.userid;


--
-- Name: calendarevent eventid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendarevent ALTER COLUMN eventid SET DEFAULT nextval('public.calendarevent_eventid_seq'::regclass);


--
-- Name: caregiver caregiverid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caregiver ALTER COLUMN caregiverid SET DEFAULT nextval('public.caregiver_caregiverid_seq'::regclass);


--
-- Name: conversation interactionid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.conversation ALTER COLUMN interactionid SET DEFAULT nextval('public.conversation_interactionid_seq'::regclass);


--
-- Name: emotionrecord emotionid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.emotionrecord ALTER COLUMN emotionid SET DEFAULT nextval('public.emotionrecord_emotionid_seq'::regclass);


--
-- Name: faceencoding faceencodingid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faceencoding ALTER COLUMN faceencodingid SET DEFAULT nextval('public.faceencoding_faceencodingid_seq'::regclass);


--
-- Name: knownperson personid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knownperson ALTER COLUMN personid SET DEFAULT nextval('public.knownperson_personid_seq'::regclass);


--
-- Name: note noteid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.note ALTER COLUMN noteid SET DEFAULT nextval('public.note_noteid_seq'::regclass);


--
-- Name: users userid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN userid SET DEFAULT nextval('public.users_userid_seq'::regclass);


--
-- Name: calendarevent calendarevent_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendarevent
    ADD CONSTRAINT calendarevent_pkey PRIMARY KEY (eventid);


--
-- Name: caregiver caregiver_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caregiver
    ADD CONSTRAINT caregiver_pkey PRIMARY KEY (caregiverid);


--
-- Name: conversation conversation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_pkey PRIMARY KEY (interactionid);


--
-- Name: emotionrecord emotionrecord_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.emotionrecord
    ADD CONSTRAINT emotionrecord_pkey PRIMARY KEY (emotionid);


--
-- Name: faceencoding faceencoding_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faceencoding
    ADD CONSTRAINT faceencoding_pkey PRIMARY KEY (faceencodingid);


--
-- Name: knownperson knownperson_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knownperson
    ADD CONSTRAINT knownperson_pkey PRIMARY KEY (personid);


--
-- Name: note note_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.note
    ADD CONSTRAINT note_pkey PRIMARY KEY (noteid);


--
-- Name: usercaregiver usercaregiver_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usercaregiver
    ADD CONSTRAINT usercaregiver_pkey PRIMARY KEY (userid, caregiverid);


--
-- Name: userknownperson userknownperson_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userknownperson
    ADD CONSTRAINT userknownperson_pkey PRIMARY KEY (userid, personid);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);


--
-- Name: calendarevent calendarevent_relatedpersonid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendarevent
    ADD CONSTRAINT calendarevent_relatedpersonid_fkey FOREIGN KEY (relatedpersonid) REFERENCES public.knownperson(personid);


--
-- Name: calendarevent calendarevent_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calendarevent
    ADD CONSTRAINT calendarevent_userid_fkey FOREIGN KEY (userid) REFERENCES public.users(userid);


--
-- Name: conversation conversation_personid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_personid_fkey FOREIGN KEY (personid) REFERENCES public.knownperson(personid);


--
-- Name: conversation conversation_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_userid_fkey FOREIGN KEY (userid) REFERENCES public.users(userid);


--
-- Name: emotionrecord emotionrecord_interactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.emotionrecord
    ADD CONSTRAINT emotionrecord_interactionid_fkey FOREIGN KEY (interactionid) REFERENCES public.conversation(interactionid);


--
-- Name: faceencoding faceencoding_personid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faceencoding
    ADD CONSTRAINT faceencoding_personid_fkey FOREIGN KEY (personid) REFERENCES public.knownperson(personid);


--
-- Name: note note_interactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.note
    ADD CONSTRAINT note_interactionid_fkey FOREIGN KEY (interactionid) REFERENCES public.conversation(interactionid);


--
-- Name: usercaregiver usercaregiver_caregiverid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usercaregiver
    ADD CONSTRAINT usercaregiver_caregiverid_fkey FOREIGN KEY (caregiverid) REFERENCES public.caregiver(caregiverid);


--
-- Name: usercaregiver usercaregiver_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usercaregiver
    ADD CONSTRAINT usercaregiver_userid_fkey FOREIGN KEY (userid) REFERENCES public.users(userid);


--
-- Name: userknownperson userknownperson_personid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userknownperson
    ADD CONSTRAINT userknownperson_personid_fkey FOREIGN KEY (personid) REFERENCES public.knownperson(personid);


--
-- Name: userknownperson userknownperson_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userknownperson
    ADD CONSTRAINT userknownperson_userid_fkey FOREIGN KEY (userid) REFERENCES public.users(userid);


--
-- PostgreSQL database dump complete
--

\unrestrict dIfMbyfHqenEi4LAyfovhjxluOCmkoHDyE0jveEUpM9fniTR7fd9OCINOUCAd7g