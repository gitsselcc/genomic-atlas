export interface Area { id: string; name: string; description: string; subareas: string[]; }
export interface Institution { id: string; name: string; country: string; city?: string; website: string; }
export interface Laboratory { id: string; institution_id: string; name: string; research_area_ids: string[]; website: string; contact_url?: string; }
export interface Opportunity {
 id: string; title: string; type: 'summer'|'research_stay'|'research_year'|'congress'|'seminar'|'workshop'|'course'|'fellowship'|'mobility';
 institution_id: string; research_area_ids: string[]; level: ('undergraduate'|'master'|'phd')[];
 official_url: string; description: string; verification_status: 'verified'|'pending'|'outdated'; last_verified?: string;
}
export interface Call {id: string; opportunity_id: string; cycle: string; opens_at?: string|null; closes_at?: string|null; starts_at?: string|null; ends_at?: string|null; source_url: string;}
export interface Funding {id: string; opportunity_id: string; type: 'full'|'partial'|'none'|'unknown'; details: string; source_url: string;}
