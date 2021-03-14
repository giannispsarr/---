create table if not exists organizations
(
	id uuid not null
		constraint organizations_pk
			primary key,
	label varchar(128) not null,
	abbreviation varchar,
	latin_name varchar,
	status varchar,
	category varchar,
	vat_number integer,
	fek_number varchar,
	fek_issue varchar,
	fek_year integer,
	ode_manager_email varchar,
	website varchar,
	supervisor_id integer,
	supervisor_label varchar,
	active boolean default true not null
);

alter table organizations owner to postdbaegis;

create unique index if not exists organizations_id_uindex
	on organizations (id);

create table if not exists decisions
(
	id uuid not null
		constraint decisions_pk
			primary key,
	"decisionType_id" uuid,
	organization_id uuid
		constraint decisions_organizations_id_fk
			references organizations,
	subject varchar,
	ada varchar,
	status varchar,
	url varchar,
	"documentUrl" varchar,
	"documentChecksum" varchar,
	"submissionTimestamp" timestamp,
	"issueDate" timestamp not null
);

alter table decisions owner to postdbaegis;

create table if not exists attachments
(
	id uuid not null
		constraint attachments_pk
			primary key,
	filename varchar,
	description varchar,
	mime_type varchar,
	checksum varchar,
	size integer default 1 not null,
	active boolean default true not null,
	decision_id uuid not null
		constraint attachments_decisions_id_fk
			references decisions
);

alter table attachments owner to postdbaegis;

create unique index if not exists attachments_id_uindex
	on attachments (id);

create unique index if not exists decisions_id_uindex
	on decisions (id);

create table if not exists decision_types
(
	id uuid not null
		constraint decision_types_pk
			primary key,
	label varchar,
	parent varchar,
	"allowedInDecisions" boolean default true not null,
	decision_type_parent_id uuid
		constraint decision_types_decision_types_id_fk
			references decision_types
);

alter table decision_types owner to postdbaegis;

create unique index if not exists decision_types_id_uindex
	on decision_types (id);

create table if not exists signers
(
	id uuid not null
		constraint signers_pk
			primary key,
	"firstName" varchar,
	"lastName" varchar,
	active boolean default true not null,
	"activeFrom" timestamp default now() not null,
	"activeUntil" timestamp default now() not null,
	organization_id uuid
		constraint signers_organizations_id_fk
			references organizations,
	"hasOrganizationSignRights" boolean default true not null,
	decision_id uuid
		constraint signers_decisions_id_fk
			references decisions
				on update cascade on delete cascade
);

alter table signers owner to postdbaegis;

create unique index if not exists signers_id_uindex
	on signers (id);

create table if not exists units
(
	id uuid not null
		constraint units_pk
			primary key,
	label varchar,
	abbreviation varchar,
	active boolean default true not null,
	"activeFrom" timestamp default now() not null,
	"activeUntil" timestamp default now() not null,
	category varchar
);

alter table units owner to postdbaegis;

create unique index if not exists units_id_uindex
	on units (id);

create table if not exists signers_units
(
	id uuid not null
		constraint signers_units_pk
			primary key,
	property varchar not null,
	signer_id uuid not null
		constraint signers_units_signers_id_fk
			references signers,
	unit_id uuid not null
		constraint signers_units_units_id_fk
			references units
				on update cascade on delete cascade
);

alter table signers_units owner to postdbaegis;

create unique index if not exists signers_units_id_uindex
	on signers_units (id);

create table if not exists organization_details
(
	id uuid,
	unit_id uuid not null
		constraint organization_details_units_id_fk
			references units,
	organization_id uuid not null
		constraint organization_details_organizations_id_fk
			references organizations
);

alter table organization_details owner to postdbaegis;

create table if not exists decisions_category
(
	id uuid not null
		constraint decisions_category_pk
			primary key,
	decision_id uuid not null
		constraint decisions_category_decisions_id_fk
			references decisions,
	decision_type_id uuid not null
		constraint decisions_category_decision_types_id_fk
			references decision_types
);

alter table decisions_category owner to postdbaegis;

create unique index if not exists decisions_category_id_uindex
	on decisions_category (id);

create table if not exists decisions_units
(
	id uuid not null
		constraint decisions_units_pk
			primary key,
	unit_id uuid not null
		constraint decisions_units_units_id_fk
			references units
				on update cascade on delete cascade,
	decision_id uuid not null
		constraint decisions_units_decisions_id_fk
			references decisions
				on update cascade on delete cascade
);

alter table decisions_units owner to postdbaegis;

create unique index if not exists decisions_units_id_uindex
	on decisions_units (id);

