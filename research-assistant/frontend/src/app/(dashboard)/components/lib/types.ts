export type TrustCategory = 'evidence' | 'inference' | 'forecast' | 'hypothesis';

export type Confidence = 'high' | 'medium' | 'low';

export interface ResearchProject {
  id: string;
  title: string;
  question: string;
  description: string;
  paperCount: number;
  evidenceCount: number;
  topicCount: number;
  updatedAt: string;
  topics: string[];
  signals: Signal[];
  recentDiscoveries: RecentDiscovery[];
  frontier: FrontierTopic[];
  status: 'active' | 'paused' | 'archived';
}

export interface Signal {
  label: string;
  change: number;
  direction: 'up' | 'down' | 'flat';
}

export interface RecentDiscovery {
  type: 'connection' | 'contradiction' | 'opportunity';
  count: number;
  description: string;
}

export interface FrontierTopic {
  name: string;
  momentum: number;
  convergence: number;
  novelty: number;
  forecast: 'high' | 'medium' | 'low';
  confidence: Confidence;
  reasons: string[];
  supportingEvidence: number;
  counterSignals: number;
  relevantPapers: number;
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  venue: string;
  year: number;
  abstract: string;
  tags: string[];
  citations: number;
  doi?: string;
  method?: string;
  dataset?: string;
  relevance?: number;
  addedAt?: string;
  trustCategory?: TrustCategory;
}

export interface Evidence {
  id: string;
  quote: string;
  paperId: string;
  paperTitle: string;
  section: string;
  page: number;
  relevance: number;
  category: 'primary' | 'secondary' | 'contextual';
  trustCategory: TrustCategory;
}

export interface ContradictionClaim {
  claim: string;
  supporting: number;
  contradicting: number;
  qualifying: number;
  reasons: string[];
  papers: { title: string; stance: 'support' | 'contradict' | 'qualify'; note: string }[];
}

export interface ResearchGap {
  id: string;
  combination: string[];
  relatedPapers: number;
  density: 'low' | 'medium' | 'high';
  opportunity: 'high' | 'medium' | 'low';
  observed: boolean;
  description: string;
}

export interface Opportunity {
  id: string;
  title: string;
  subtitle: string;
  novelty: number;
  momentum: number;
  competition: number;
  difficulty: number;
  relatedPapers: number;
  recentGrowth: number;
}

export interface Hypothesis {
  id: string;
  statement: string;
  evidence: string;
  gap: string;
  whyItMatters: string;
  potentialContribution: string;
  method: string;
  dataset: string;
  baseline: string;
  metrics: string[];
  status: 'draft' | 'testing' | 'validated' | 'falsified';
}

export interface RoadmapStep {
  id: string;
  label: string;
  value: string;
  type: 'gap' | 'question' | 'hypothesis' | 'methodology' | 'dataset' | 'baseline' | 'experiment' | 'evaluation' | 'contribution';
}

export interface ReportSection {
  id: string;
  title: string;
  content: string;
}

export interface Collection {
  id: string;
  name: string;
  count: number;
  papers: Paper[];
}

export interface TrendPoint {
  period: string;
  value: number;
}

export interface TrendSeries {
  id: string;
  label: string;
  color: string;
  data: TrendPoint[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'paper' | 'topic' | 'method' | 'author' | 'dataset';
  x: number;
  y: number;
  size: number;
  connections: number;
}

export interface GraphEdge {
  from: string;
  to: string;
  type: 'citation' | 'similarity' | 'shared-method' | 'shared-dataset' | 'conceptual';
  strength: number;
}

export interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  trustCategory?: TrustCategory;
  evidence?: Evidence[];
  interpretation?: string;
  counterEvidence?: string;
  relatedPapers?: string[];
  nextQuestions?: string[];
}

export interface ProcessingStep {
  label: string;
  status: 'done' | 'active' | 'pending';
}
