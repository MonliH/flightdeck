// types.ts
export interface TeamMember {
  name: string;
  profile_url: string;
}

export interface ParsedContent {
  url: string;
  description_markdown: string;
  built_with: string[];
  links: {
    title: string;
    url: string;
  }[];
  submissions: {
    name: string;
    url: string;
    awards: string[];
  }[];
  scraped_at: string;
}

export interface Project {
  title: string;
  tagline: string;
  project_url: string;
  thumbnail_url: string;
  likes: number;
  comments: number;
  team_members: TeamMember[];
  is_winner: boolean;
  parsed_content: ParsedContent;
}

// Array tuple of [similarity score, project]
export type SimilarityResult = [number, Project];
