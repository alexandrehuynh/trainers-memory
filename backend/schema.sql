-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Create clients table
CREATE TABLE public.clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    notes TEXT,
    trainer_id UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(email, trainer_id)
);

-- Enable Row Level Security
ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;

-- Create policy for trainers to access their own clients
CREATE POLICY "Trainers can manage their own clients" ON public.clients
    USING (trainer_id = auth.uid())
    WITH CHECK (trainer_id = auth.uid());

-- Create workout_records table
CREATE TABLE public.workout_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    exercise TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight NUMERIC(10, 2) NOT NULL,
    notes TEXT,
    modifiers TEXT,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Enable Row Level Security
ALTER TABLE public.workout_records ENABLE ROW LEVEL SECURITY;

-- Create policy for trainers to access workout records for their clients
CREATE POLICY "Trainers can manage workout records for their clients" ON public.workout_records
    USING (client_id IN (SELECT id FROM public.clients WHERE trainer_id = auth.uid()))
    WITH CHECK (client_id IN (SELECT id FROM public.clients WHERE trainer_id = auth.uid()));

-- Create voice_notes table
CREATE TABLE public.voice_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES public.clients(id) ON DELETE CASCADE,
    trainer_id UUID NOT NULL REFERENCES auth.users(id),
    date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    audio_url TEXT NOT NULL,
    transcript TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.voice_notes ENABLE ROW LEVEL SECURITY;

-- Create policy for trainers to access voice notes for their clients
CREATE POLICY "Trainers can manage voice notes for their clients" ON public.voice_notes
    USING (trainer_id = auth.uid())
    WITH CHECK (trainer_id = auth.uid());

-- Create indices for performance
CREATE INDEX idx_clients_trainer_id ON public.clients(trainer_id);
CREATE INDEX idx_workout_records_client_id ON public.workout_records(client_id);
CREATE INDEX idx_workout_records_date ON public.workout_records(date);
CREATE INDEX idx_voice_notes_client_id ON public.voice_notes(client_id);
CREATE INDEX idx_voice_notes_trainer_id ON public.voice_notes(trainer_id); 