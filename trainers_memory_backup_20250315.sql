--
-- PostgreSQL database dump
--

-- Dumped from database version 15.12 (Homebrew)
-- Dumped by pg_dump version 15.12 (Homebrew)

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO alexhuynh;

--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.api_keys (
    id uuid NOT NULL,
    key character varying(255) NOT NULL,
    client_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    last_used_at timestamp without time zone,
    expires_at timestamp without time zone
);


ALTER TABLE public.api_keys OWNER TO alexhuynh;

--
-- Name: clients; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.clients (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(20),
    notes text,
    api_key character varying(255),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.clients OWNER TO alexhuynh;

--
-- Name: exercises; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.exercises (
    id uuid NOT NULL,
    workout_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    sets integer NOT NULL,
    reps integer NOT NULL,
    weight double precision NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.exercises OWNER TO alexhuynh;

--
-- Name: template_exercises; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.template_exercises (
    id uuid NOT NULL,
    template_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    sets integer NOT NULL,
    reps integer NOT NULL,
    weight double precision,
    notes text
);


ALTER TABLE public.template_exercises OWNER TO alexhuynh;

--
-- Name: users; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255),
    role character varying(50) DEFAULT 'trainer'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO alexhuynh;

--
-- Name: workout_templates; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.workout_templates (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    type character varying(255) NOT NULL,
    duration integer NOT NULL,
    is_system boolean DEFAULT false NOT NULL,
    user_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.workout_templates OWNER TO alexhuynh;

--
-- Name: workouts; Type: TABLE; Schema: public; Owner: alexhuynh
--

CREATE TABLE public.workouts (
    id uuid NOT NULL,
    client_id uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    type character varying(255) NOT NULL,
    duration integer NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.workouts OWNER TO alexhuynh;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.alembic_version (version_num) FROM stdin;
062832f6fa7c
\.


--
-- Data for Name: api_keys; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.api_keys (id, key, client_id, name, description, active, created_at, last_used_at, expires_at) FROM stdin;
00000000-0000-0000-0000-000000000099	test_key_12345	00000000-0000-0000-0000-000000000001	Test API Key	For development and testing	t	2025-03-08 18:06:22.81346	2025-03-11 02:22:34.302612	\N
6e0dc764-3720-4aa5-bc09-ba4f40bff3f1	tmk_3db7baed7f1c40bb9e39b9c512fdcf8d	40cae841-936d-4468-bc81-31d95c305c92	Test API Key	\N	t	2025-03-11 21:26:00.181208	\N	\N
924d06ca-0afb-45b0-a109-f748a493ffbf	tmk_f9327e1428324b4aae3e74607a58284f	a5a939ae-f92b-4a1d-a634-ef7cf550e2d8	Swagger Testing Key	\N	t	2025-03-11 15:04:01.744429	\N	\N
8360ea1e-0ff8-485f-a231-07cb10ed036c	tmk_40af9844458144dc9ba5f5859c8b0f01	3c00ccc2-a59b-405a-8d80-51ed9f86d871	Swagger Testing Key	\N	t	2025-03-11 15:07:43.773619	\N	\N
\.


--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.clients (id, name, email, phone, notes, api_key, created_at, updated_at) FROM stdin;
00000000-0000-0000-0000-000000000002	Jane Smith	jane@example.com	555-987-6543	Prefers morning sessions	\N	2025-03-08 18:06:22.806885	2025-03-11 02:18:26.37595
00000000-0000-0000-0000-000000000001	Alex Huynh	alex.va.huynh@gmail.com	9255193662	He is the dopest person ever	\N	2025-03-08 18:06:22.806885	2025-03-11 04:14:28.947043
00000000-0000-0000-0000-000000000003	Chad Ochocinco	iwasallthewayin@staywithmenow.pp	0850032011	Told to go deeper but he was already all the way in. Focused on perfecting his craft in the pelvis region	\N	2025-03-08 18:06:22.806885	2025-03-11 19:28:06.567568
3c00ccc2-a59b-405a-8d80-51ed9f86d871	Test Client	test-20250311150743@example.com	555-123-4567	\N	\N	2025-03-11 15:07:43.770771	2025-03-11 15:07:43.770775
9140d62a-1efb-44e1-86d7-6b818bab142c	John Doe	john.doe@example.com	555-123-4567	New client interested in strength training	\N	2025-03-11 22:13:55.032566	2025-03-11 22:13:55.03257
1a2687fd-f608-4f01-a45c-b3711c6b15c8	John Howdy	john.Howdy@example.com	555-123-4567	New client interested in strength training	\N	2025-03-11 22:14:11.8838	2025-03-11 22:14:11.883804
b576c2c6-6510-49ef-985a-7c6e6786c889	Phil Tran	philly@example.com	555-5427	Created via test script	\N	2025-03-11 21:38:44.200914	2025-03-11 22:49:17.749954
40cae841-936d-4468-bc81-31d95c305c92	Pauline Evangelista	pauline@example.com	555-123-4567	she's a 10 but she thinks keeping nudes are bad.	\N	2025-03-11 21:26:00.174584	2025-03-11 22:49:43.543799
a5a939ae-f92b-4a1d-a634-ef7cf550e2d8	Lily Huynh	test-20250311150401@example.com	555-123-4567	She's family	\N	2025-03-11 15:04:01.741607	2025-03-11 22:49:57.779636
aeb49b39-4d02-4ae3-9d89-3783d8e48549	Lam Huynh	lam@example.com	555-123-4567	Is a size 34 not 36	\N	2025-03-11 22:58:23.113727	2025-03-11 22:58:23.113734
\.


--
-- Data for Name: exercises; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.exercises (id, workout_id, name, sets, reps, weight, notes, created_at, updated_at) FROM stdin;
00000000-0000-0000-0000-000000000027	00000000-0000-0000-0000-000000000013	Downward Dog	1	5	0	Hold 30 seconds each	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
00000000-0000-0000-0000-000000000028	00000000-0000-0000-0000-000000000013	Hamstring Stretch	2	4	0	Hold 45 seconds each side	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
00000000-0000-0000-0000-000000000029	00000000-0000-0000-0000-000000000014	Crunches	3	20	0	\N	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
00000000-0000-0000-0000-000000000030	00000000-0000-0000-0000-000000000014	Plank	3	1	0	Hold for 60 seconds	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
00000000-0000-0000-0000-000000000031	00000000-0000-0000-0000-000000000015	Distance Run	1	1	0	5km at steady pace	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
00000000-0000-0000-0000-000000000032	00000000-0000-0000-0000-000000000015	Cool Down Walk	1	1	0	10 minutes	2025-03-08 18:06:22.81204	2025-03-08 18:06:22.81204
66e2d3b1-5b68-43dc-b506-2f7c2a9f3523	00000000-0000-0000-0000-000000000012	Treadmill Sprint	5	1	0	1 min sprint, 1 min rest	2025-03-09 02:33:46.188767	2025-03-09 02:33:46.18877
cdb9e7fb-685b-40bf-b8eb-3d7db4b5a550	00000000-0000-0000-0000-000000000012	Jumping Jacks	3	30	0	\N	2025-03-09 02:33:46.19094	2025-03-09 02:33:46.190942
d8694f90-1507-47c0-a489-df7d29d38405	00000000-0000-0000-0000-000000000012	Burpees	4	15	0	Modified due to wrist pain	2025-03-09 02:33:46.192147	2025-03-09 02:33:46.192149
928fa3df-eaf5-4c33-8b94-821d207b0484	00000000-0000-0000-0000-000000000011	Bench Press	3	10	133	Increase weight next time	2025-03-11 05:33:46.113425	2025-03-11 05:33:46.113428
e685017e-bf9b-4888-bba1-259b69b3f91b	00000000-0000-0000-0000-000000000011	Lat Pulldown	3	12	120		2025-03-11 05:33:46.114944	2025-03-11 05:33:46.114947
fc040ec9-18f9-452d-a5cb-aa97b2f3cfe0	00000000-0000-0000-0000-000000000011	Bicep Curls	3	12	25	Slow reps	2025-03-11 05:33:46.116048	2025-03-11 05:33:46.116051
bd32608f-9304-4f62-bc83-274efa9453a4	00000000-0000-0000-0000-000000000011	handstand pushups	3	10	0		2025-03-11 05:33:46.117221	2025-03-11 05:33:46.117223
109da9be-fefd-447d-84a3-9ad22105379e	e66281d7-3772-4eb1-9a90-fbc4c3b7466d	Backbend	3	10	0	This was more for time.	2025-03-11 19:23:38.622342	2025-03-11 19:23:38.622346
1ecf1fc5-ed7a-470f-ab5a-8ee2ac513ac9	e66281d7-3772-4eb1-9a90-fbc4c3b7466d	Handstand	3	10	0	this is for time	2025-03-11 19:23:38.624965	2025-03-11 19:23:38.624968
ec59b550-3568-4c4a-b8ad-257f26b0537f	0dfd2276-26ff-4cb4-8cc5-c96be8c31385	Isometric Testing	3	10	0		2025-03-13 03:39:54.016511	2025-03-13 03:39:54.016516
52869d51-0b64-4742-b15e-7b44a115fad4	0dfd2276-26ff-4cb4-8cc5-c96be8c31385	Eccentric Negatives	3	10	0		2025-03-13 03:39:54.018169	2025-03-13 03:39:54.018171
2f88c6a6-ae99-47c0-9e77-9024cf4283da	0931761e-9e66-482b-82ed-30ac5bb1532b	Surgery	3	10	0		2025-03-13 03:40:24.323688	2025-03-13 03:40:24.323691
2e6892ec-c1cc-44ff-b974-dae97eaf1ebc	0931761e-9e66-482b-82ed-30ac5bb1532b	Pelvis Thrust	3	10	0		2025-03-13 03:40:24.324867	2025-03-13 03:40:24.324869
\.


--
-- Data for Name: template_exercises; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.template_exercises (id, template_id, name, sets, reps, weight, notes) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.users (id, email, hashed_password, role, is_active, created_at, updated_at) FROM stdin;
00000000-0000-0000-0000-000000000001	admin@trainersmemory.com	\N	admin	t	2025-03-15 19:21:44.267885	\N
\.


--
-- Data for Name: workout_templates; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.workout_templates (id, name, description, type, duration, is_system, user_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workouts; Type: TABLE DATA; Schema: public; Owner: alexhuynh
--

COPY public.workouts (id, client_id, date, type, duration, notes, created_at, updated_at) FROM stdin;
00000000-0000-0000-0000-000000000013	00000000-0000-0000-0000-000000000003	2024-03-06 09:00:00	Flexibility	30	Yoga and stretching	2025-03-08 18:06:22.810447	2025-03-08 18:06:22.810447
00000000-0000-0000-0000-000000000014	00000000-0000-0000-0000-000000000001	2024-03-05 11:00:00	Core	45	Focus on abs and lower back	2025-03-08 18:06:22.810447	2025-03-08 18:06:22.810447
00000000-0000-0000-0000-000000000015	00000000-0000-0000-0000-000000000002	2024-03-04 16:00:00	Endurance	75	Long distance running prep	2025-03-08 18:06:22.810447	2025-03-08 18:06:22.810447
00000000-0000-0000-0000-000000000012	00000000-0000-0000-0000-000000000002	2024-03-07 00:00:00	Cardio	45	HIIT session	2025-03-08 18:06:22.810447	2025-03-09 02:33:46.18196
00000000-0000-0000-0000-000000000011	00000000-0000-0000-0000-000000000001	2024-03-08 00:00:00	Strength Training	60	Focused on upper body	2025-03-08 18:06:22.810447	2025-03-11 05:33:46.106325
e66281d7-3772-4eb1-9a90-fbc4c3b7466d	00000000-0000-0000-0000-000000000001	2025-03-11 00:00:00	Mind-Body Connection	60	This is all about mind body connection and feeling	2025-03-11 18:57:20.739034	2025-03-11 19:23:38.615319
0dfd2276-26ff-4cb4-8cc5-c96be8c31385	3c00ccc2-a59b-405a-8d80-51ed9f86d871	2025-03-13 00:00:00	Testing	60		2025-03-13 03:39:54.014228	2025-03-13 03:39:54.014231
0931761e-9e66-482b-82ed-30ac5bb1532b	00000000-0000-0000-0000-000000000003	2025-03-13 00:00:00	Perfected Pelvis Craft	60		2025-03-13 03:40:24.322374	2025-03-13 03:40:24.322378
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_keys api_keys_key_key; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_key_key UNIQUE (key);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: clients clients_api_key_key; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_api_key_key UNIQUE (api_key);


--
-- Name: clients clients_email_key; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_email_key UNIQUE (email);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: exercises exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_pkey PRIMARY KEY (id);


--
-- Name: template_exercises template_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.template_exercises
    ADD CONSTRAINT template_exercises_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: workout_templates workout_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.workout_templates
    ADD CONSTRAINT workout_templates_pkey PRIMARY KEY (id);


--
-- Name: workouts workouts_pkey; Type: CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_pkey PRIMARY KEY (id);


--
-- Name: ix_api_keys_client_id; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_api_keys_client_id ON public.api_keys USING btree (client_id);


--
-- Name: ix_api_keys_key; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_api_keys_key ON public.api_keys USING btree (key);


--
-- Name: ix_clients_email; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_clients_email ON public.clients USING btree (email);


--
-- Name: ix_clients_name; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_clients_name ON public.clients USING btree (name);


--
-- Name: ix_exercises_workout_id; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_exercises_workout_id ON public.exercises USING btree (workout_id);


--
-- Name: ix_template_exercises_template_id; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_template_exercises_template_id ON public.template_exercises USING btree (template_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_workouts_client_id; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_workouts_client_id ON public.workouts USING btree (client_id);


--
-- Name: ix_workouts_date; Type: INDEX; Schema: public; Owner: alexhuynh
--

CREATE INDEX ix_workouts_date ON public.workouts USING btree (date);


--
-- Name: api_keys api_keys_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: exercises exercises_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: template_exercises template_exercises_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.template_exercises
    ADD CONSTRAINT template_exercises_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.workout_templates(id) ON DELETE CASCADE;


--
-- Name: workout_templates workout_templates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.workout_templates
    ADD CONSTRAINT workout_templates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: workouts workouts_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: alexhuynh
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

