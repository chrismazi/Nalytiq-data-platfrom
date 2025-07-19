import Link from "next/link"
import Image from "next/image"
import { ArrowRight, BarChart3, Bot, FileSpreadsheet, FileText, Lock, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-30 w-full border-b bg-background">
        <div className="container flex h-16 items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary text-primary-foreground font-bold">
              N
            </div>
            <div>
              <h3 className="font-semibold">NISR Rwanda</h3>
              <p className="text-xs text-muted-foreground">Data Platform</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="#features" className="text-sm font-medium hover:text-primary">
              Features
            </Link>
            <Link href="#how-it-works" className="text-sm font-medium hover:text-primary">
              How It Works
            </Link>
            <Link href="#testimonials" className="text-sm font-medium hover:text-primary">
              Testimonials
            </Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="outline">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-background">
        <div className="container px-4 md:px-6">
          <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 items-center">
            <div className="flex flex-col justify-center space-y-4">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl">
                  Rwanda&apos;s Intelligent Data Platform
                </h1>
                <p className="max-w-[600px] text-muted-foreground md:text-xl">
                  Empowering data scientists, statisticians, policymakers, and public servants with AI-powered analytics
                  and insights.
                </p>
              </div>
              <div className="flex flex-col gap-2 min-[400px]:flex-row">
                <Link href="/register">
                  <Button size="lg" className="gap-1">
                    Get Started <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
            <div className="mx-auto lg:mx-0 relative">
              <div className="relative h-[350px] w-[450px] rounded-lg overflow-hidden border shadow-xl">
                <Image
                  src="/placeholder.svg?height=700&width=900"
                  alt="Dashboard Preview"
                  fill
                  className="object-cover"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-background/20"></div>
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="bg-background/90 backdrop-blur-sm p-4 rounded-lg border shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="h-5 w-5 text-primary" />
                      <h3 className="font-medium">Real-time Analytics</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Interactive dashboards with AI-powered insights from national datasets
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="w-full py-12 md:py-24 lg:py-32">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <div className="inline-block rounded-lg bg-primary/10 px-3 py-1 text-sm text-primary">Features</div>
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">
                Powerful Tools for Data-Driven Decisions
              </h2>
              <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                Our platform combines cutting-edge AI with robust statistical tools to transform how Rwanda uses data.
              </p>
            </div>
          </div>
          <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 mt-12">
            {[
              {
                icon: <Upload className="h-10 w-10 text-primary" />,
                title: "Automated Data Processing",
                description:
                  "Upload datasets in various formats (CSV, Excel, Stata) and let our AI handle cleaning and analysis.",
              },
              {
                icon: <BarChart3 className="h-10 w-10 text-primary" />,
                title: "Interactive Dashboards",
                description: "Visualize complex data with beautiful, interactive charts and customizable dashboards.",
              },
              {
                icon: <Bot className="h-10 w-10 text-primary" />,
                title: "AI Assistant",
                description:
                  "Chat with your data using our AI assistant trained on NISR's knowledge base and your uploaded documents.",
              },
              {
                icon: <FileText className="h-10 w-10 text-primary" />,
                title: "Automated Reports",
                description:
                  "Generate comprehensive reports with AI-written narratives explaining trends and insights.",
              },
              {
                icon: <FileSpreadsheet className="h-10 w-10 text-primary" />,
                title: "Advanced Analysis",
                description:
                  "Create frequency tables, cross-tabulations, and statistical models with just a few clicks.",
              },
              {
                icon: <Lock className="h-10 w-10 text-primary" />,
                title: "Secure Access",
                description: "Role-based access ensures data security while enabling collaboration across departments.",
              },
            ].map((feature, index) => (
              <Card key={index} className="border-0 shadow-md">
                <CardHeader>
                  <div className="p-2 w-fit rounded-lg bg-primary/10 mb-2">{feature.icon}</div>
                  <CardTitle>{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="w-full py-12 md:py-24 lg:py-32 bg-muted/50">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <div className="inline-block rounded-lg bg-primary/10 px-3 py-1 text-sm text-primary">How It Works</div>
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">Simple, Powerful Workflow</h2>
              <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                Our platform streamlines the entire data lifecycle from upload to insight.
              </p>
            </div>
          </div>

          <div className="mx-auto grid max-w-5xl mt-12">
            <div className="relative">
              <div className="absolute left-8 top-0 bottom-0 w-[2px] bg-border"></div>
              {[
                {
                  step: "01",
                  title: "Upload Your Data",
                  description:
                    "Upload your datasets in CSV, Excel, or Stata format. Our system automatically detects the file type and prepares it for processing.",
                },
                {
                  step: "02",
                  title: "Automated Analysis",
                  description:
                    "Our AI analyzes your data, identifying patterns, outliers, and key insights without manual intervention.",
                },
                {
                  step: "03",
                  title: "Interactive Exploration",
                  description:
                    "Explore your data through interactive dashboards, create custom visualizations, and generate tables.",
                },
                {
                  step: "04",
                  title: "Chat With Your Data",
                  description:
                    "Ask questions about your data in natural language and receive instant insights from our AI assistant.",
                },
                {
                  step: "05",
                  title: "Generate Reports",
                  description:
                    "Create comprehensive reports with AI-generated narratives explaining the trends and insights in your data.",
                },
              ].map((item, index) => (
                <div key={index} className="relative pl-16 pb-12">
                  <div className="absolute left-0 top-0 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-bold">{item.title}</h3>
                  <p className="mt-2 text-muted-foreground">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="w-full py-12 md:py-24 lg:py-32">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <div className="inline-block rounded-lg bg-primary/10 px-3 py-1 text-sm text-primary">Testimonials</div>
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">Trusted by Experts</h2>
              <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                See what data professionals and policymakers have to say about our platform.
              </p>
            </div>
          </div>

          <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 mt-12">
            {[
              {
                quote:
                  "This platform has transformed how we analyze survey data. What used to take weeks now takes hours, with better insights.",
                name: "Dr. Jean Mugabo",
                title: "Lead Statistician, Ministry of Health",
              },
              {
                quote:
                  "The AI assistant is remarkable. I can ask complex questions about economic trends and get instant, accurate answers.",
                name: "Marie Uwase",
                title: "Economic Advisor, Office of the President",
              },
              {
                quote:
                  "As a policymaker, having access to this level of data analysis has been invaluable for evidence-based decision making.",
                name: "Emmanuel Nkusi",
                title: "Director of Planning, Ministry of Education",
              },
            ].map((testimonial, index) => (
              <Card key={index} className="border-0 shadow-md">
                <CardHeader>
                  <CardDescription className="text-base italic">&ldquo;{testimonial.quote}&rdquo;</CardDescription>
                </CardHeader>
                <CardFooter>
                  <div>
                    <p className="font-medium">{testimonial.name}</p>
                    <p className="text-sm text-muted-foreground">{testimonial.title}</p>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full py-12 md:py-24 lg:py-32 bg-primary text-primary-foreground">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tighter md:text-4xl">Ready to Transform Your Data?</h2>
              <p className="max-w-[600px] text-primary-foreground/80 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                Join Rwanda's leading institutions already using our platform to drive data-informed decisions.
              </p>
            </div>
            <div className="flex flex-col gap-2 min-[400px]:flex-row">
              <Link href="/register">
                <Button size="lg" variant="secondary" className="gap-1">
                  Get Started <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="bg-transparent text-primary-foreground border-primary-foreground hover:bg-primary-foreground/10"
                >
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full py-6 md:py-12 border-t">
        <div className="container px-4 md:px-6">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary text-primary-foreground font-bold">
                  N
                </div>
                <div>
                  <h3 className="font-semibold">NISR Rwanda</h3>
                  <p className="text-xs text-muted-foreground">Data Platform</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                National Institute of Statistics of Rwanda
                <br />
                Kigali, Rwanda
              </p>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Platform</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#features" className="text-muted-foreground hover:text-foreground">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#how-it-works" className="text-muted-foreground hover:text-foreground">
                    How It Works
                  </Link>
                </li>
                <li>
                  <Link href="#testimonials" className="text-muted-foreground hover:text-foreground">
                    Testimonials
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    API
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    Support
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground">
                    Data Policy
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 border-t pt-8 text-center text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} National Institute of Statistics of Rwanda. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
