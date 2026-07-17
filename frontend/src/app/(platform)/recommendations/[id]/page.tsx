import type { Metadata } from "next";
import { RecommendationDetailView } from "@/features/recommendations/components/recommendation-detail-view";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return { title: `Recommendation ${id}` };
}

export default async function RecommendationDetailPage({ params }: Props) {
  const { id } = await params;
  return <RecommendationDetailView id={id} />;
}
