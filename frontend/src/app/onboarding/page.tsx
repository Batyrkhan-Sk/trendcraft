import { OnboardingFlow } from "@/components/onboarding/onboarding-flow";
import { getProfile } from "@/lib/api";

export const metadata = { title: "Onboarding" };
export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const profile = await getProfile();
  return <OnboardingFlow initial={profile} />;
}
