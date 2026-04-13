import { Header } from "@/components/header";
import { Hero } from "@/components/hero";
import { RecentReports } from "@/components/recent-reports";
import { PipelineOverview } from "@/components/pipeline-overview";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1">
        <Hero />
        <PipelineOverview />
        <RecentReports />
      </main>
      <Footer />
    </div>
  );
}
