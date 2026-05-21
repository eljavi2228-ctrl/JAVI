-- Control Estadistico de Procesos para frutas y hortalizas
-- Ejecutar en Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.productos (
  id uuid primary key default gen_random_uuid(),
  nombre text not null unique,
  tipo text not null check (tipo in ('Fruta', 'Hortaliza', 'Otro')),
  created_at timestamptz not null default now()
);

create table if not exists public.variables_continuas (
  id uuid primary key default gen_random_uuid(),
  producto_id uuid not null references public.productos(id) on delete cascade,
  nombre_variable text not null,
  unidad text not null,
  created_at timestamptz not null default now(),
  unique (producto_id, nombre_variable)
);

create table if not exists public.atributos (
  id uuid primary key default gen_random_uuid(),
  producto_id uuid not null references public.productos(id) on delete cascade,
  nombre_atributo text not null,
  tipo_inspeccion text not null check (tipo_inspeccion in ('p', 'np', 'c', 'u')),
  created_at timestamptz not null default now(),
  unique (producto_id, nombre_atributo)
);

create table if not exists public.subgrupos (
  id uuid primary key default gen_random_uuid(),
  producto_id uuid not null references public.productos(id) on delete cascade,
  fecha_hora timestamptz not null default now(),
  analista text not null,
  lote text not null,
  tamano_muestra integer not null default 1 check (tamano_muestra > 0),
  unidades_inspeccionadas integer not null default 1 check (unidades_inspeccionadas > 0),
  created_at timestamptz not null default now()
);

create table if not exists public.mediciones (
  id uuid primary key default gen_random_uuid(),
  subgrupo_id uuid not null references public.subgrupos(id) on delete cascade,
  variable_id uuid not null references public.variables_continuas(id) on delete cascade,
  valor numeric not null,
  created_at timestamptz not null default now()
);

create table if not exists public.inspecciones_atributos (
  id uuid primary key default gen_random_uuid(),
  subgrupo_id uuid not null references public.subgrupos(id) on delete cascade,
  atributo_id uuid not null references public.atributos(id) on delete cascade,
  conforma boolean not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_variables_producto on public.variables_continuas(producto_id);
create index if not exists idx_atributos_producto on public.atributos(producto_id);
create index if not exists idx_subgrupos_producto_fecha on public.subgrupos(producto_id, fecha_hora);
create index if not exists idx_mediciones_subgrupo on public.mediciones(subgrupo_id);
create index if not exists idx_mediciones_variable on public.mediciones(variable_id);
create index if not exists idx_inspecciones_subgrupo on public.inspecciones_atributos(subgrupo_id);
create index if not exists idx_inspecciones_atributo on public.inspecciones_atributos(atributo_id);

alter table public.productos enable row level security;
alter table public.variables_continuas enable row level security;
alter table public.atributos enable row level security;
alter table public.subgrupos enable row level security;
alter table public.mediciones enable row level security;
alter table public.inspecciones_atributos enable row level security;

-- Politicas simples para uso academico/local con anon key o usuario autenticado.
-- Si la app sera publica o multiusuario, endurecer estas politicas antes de produccion.
drop policy if exists "authenticated read productos" on public.productos;
create policy "authenticated read productos"
on public.productos for select to anon, authenticated using (true);

drop policy if exists "authenticated write productos" on public.productos;
create policy "authenticated write productos"
on public.productos for all to anon, authenticated using (true) with check (true);

drop policy if exists "authenticated read variables" on public.variables_continuas;
create policy "authenticated read variables"
on public.variables_continuas for select to anon, authenticated using (true);

drop policy if exists "authenticated write variables" on public.variables_continuas;
create policy "authenticated write variables"
on public.variables_continuas for all to anon, authenticated using (true) with check (true);

drop policy if exists "authenticated read atributos" on public.atributos;
create policy "authenticated read atributos"
on public.atributos for select to anon, authenticated using (true);

drop policy if exists "authenticated write atributos" on public.atributos;
create policy "authenticated write atributos"
on public.atributos for all to anon, authenticated using (true) with check (true);

drop policy if exists "authenticated read subgrupos" on public.subgrupos;
create policy "authenticated read subgrupos"
on public.subgrupos for select to anon, authenticated using (true);

drop policy if exists "authenticated write subgrupos" on public.subgrupos;
create policy "authenticated write subgrupos"
on public.subgrupos for all to anon, authenticated using (true) with check (true);

drop policy if exists "authenticated read mediciones" on public.mediciones;
create policy "authenticated read mediciones"
on public.mediciones for select to anon, authenticated using (true);

drop policy if exists "authenticated write mediciones" on public.mediciones;
create policy "authenticated write mediciones"
on public.mediciones for all to anon, authenticated using (true) with check (true);

drop policy if exists "authenticated read inspecciones" on public.inspecciones_atributos;
create policy "authenticated read inspecciones"
on public.inspecciones_atributos for select to anon, authenticated using (true);

drop policy if exists "authenticated write inspecciones" on public.inspecciones_atributos;
create policy "authenticated write inspecciones"
on public.inspecciones_atributos for all to anon, authenticated using (true) with check (true);
