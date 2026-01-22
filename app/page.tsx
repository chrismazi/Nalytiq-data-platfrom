"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { motion } from "framer-motion"
import {
  Check,
  ChevronRight,
  Menu,
  X,
  Moon,
  Sun,
  ArrowRight,
  BarChart3,
  Bot,
  FileSpreadsheet,
  FileText,
  Lock,
  Upload,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTheme } from "next-themes"

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const handleScroll = () => {
      if (window.scrollY > 10) {
        setIsScrolled(true)
      } else {
        setIsScrolled(false)
      }
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  }

  // Unique framer-motion variants for each section
  const heroVariant = {
    hidden: { opacity: 0, y: 40 },
    show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.42, 0, 0.58, 1] } }, // easeOut cubic-bezier
  };
  const featuresVariant = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.7, staggerChildren: 0.12 } },
  };
  const howItWorksVariant = {
    hidden: { opacity: 0, x: -60 },
    show: { opacity: 1, x: 0, transition: { duration: 0.8, staggerChildren: 0.1 } },
  };
  const faqVariant = {
    hidden: { opacity: 0, scale: 0.9 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.7, staggerChildren: 0.1 } },
  };
  const ctaVariant = {
    hidden: { opacity: 0, y: 80, scale: 0.95 },
    show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.9, ease: [0.36, 0, 0.66, -0.56] } }, // anticipate cubic-bezier
  };

  // Nalytiq-specific features
  const features = [
    {
                title: "Automated Data Processing",
      description: "Upload datasets in various formats (CSV, Excel, Stata) and let our AI handle cleaning and analysis.",
      icon: <Upload className="size-5" />,
              },
              {
                title: "Interactive Dashboards",
                description: "Visualize complex data with beautiful, interactive charts and customizable dashboards.",
      icon: <BarChart3 className="size-5" />,
              },
              {
                title: "AI Assistant",
      description: "Chat with your data using our AI assistant trained on Nalytiq's knowledge base and your uploaded documents.",
      icon: <Bot className="size-5" />,
              },
              {
                title: "Automated Reports",
      description: "Generate comprehensive reports with AI-written narratives explaining trends and insights.",
      icon: <FileText className="size-5" />,
              },
              {
                title: "Advanced Analysis",
      description: "Create frequency tables, cross-tabulations, and statistical models with just a few clicks.",
      icon: <FileSpreadsheet className="size-5" />,
              },
              {
                title: "Secure Access",
                description: "Role-based access ensures data security while enabling collaboration across departments.",
      icon: <Lock className="size-5" />,
    },
  ]

  // NISR Rwanda-specific steps
  const steps = [
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
  ]

  // NISR Rwanda-specific FAQ
  const faqs = [
    {
      question: "How secure is my data?",
      answer:
        "We use industry-standard security practices. All data is encrypted in transit and at rest. Access is role-based and auditable.",
    },
    {
      question: "Can I use my own datasets?",
      answer:
        "Yes, you can upload your own datasets in CSV, Excel, or Stata format for analysis.",
    },
    {
      question: "Is there support for government agencies?",
      answer:
        "Yes, we provide dedicated support for government agencies and public sector organizations.",
    },
    {
      question: "Can I generate automated reports?",
      answer:
        "Yes, our platform can generate comprehensive reports with AI-written narratives and visualizations.",
    },
    {
      question: "Is my data private?",
      answer:
        "Your data is private and only accessible to you and authorized team members within your organization.",
    },
  ]

  return (
    <div className="landing-theme flex min-h-[100dvh] flex-col bg-[linear-gradient(180deg,rgba(236,255,245,1)_0%,rgba(252,255,253,1)_10%,rgba(252,255,253,1)_90%,rgba(236,255,245,1)_100%)] dark:bg-[linear-gradient(180deg,rgba(2,10,8,1)_0%,rgba(4,9,8,1)_10%,rgba(4,9,8,1)_90%,rgba(2,10,8,1)_100%)]">
      {/* Header */}
      <header
        className={`sticky top-0 z-50 w-full backdrop-blur-xl transition-all duration-300 ${isScrolled ? "bg-background/75 shadow-sm border-b border-border/60" : "bg-transparent"}`}
      >
        <div className="landing-container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold">
            <div className="size-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-primary-foreground">
              N
            </div>
            <span>Nalytiq</span>
          </div>
          <nav className="hidden md:flex gap-8">
            <Link href="#features" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              Features
            </Link>
            <Link href="#how-it-works" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              How It Works
            </Link>
            <Link href="#faq" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              FAQ
            </Link>
          </nav>
          <div className="hidden md:flex gap-4 items-center">
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
              {mounted && theme === "dark" ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
              <span className="sr-only">Toggle theme</span>
            </Button>
            <Link href="/login" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              Sign In
            </Link>
            <Link href="/register">
              <Button className="rounded-full bg-gradient-to-r from-primary via-emerald-600 to-emerald-700 text-primary-foreground shadow-sm hover:opacity-95">
                Get Started
                <ChevronRight className="ml-1 size-4" />
              </Button>
            </Link>
          </div>
          <div className="flex items-center gap-4 md:hidden">
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
              {mounted && theme === "dark" ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
              <span className="sr-only">Toggle menu</span>
            </Button>
          </div>
        </div>
        {/* Mobile menu */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden absolute top-16 inset-x-0 bg-background/90 backdrop-blur-xl border-b"
          >
            <div className="landing-container py-4 flex flex-col gap-4">
              <Link href="#features" className="py-2 text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>
                Features
              </Link>
              <Link href="#how-it-works" className="py-2 text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>
                How It Works
              </Link>
              <Link href="#faq" className="py-2 text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>
                FAQ
              </Link>
              <div className="flex flex-col gap-2 pt-2 border-t">
                <Link href="/login" className="py-2 text-sm font-medium" onClick={() => setMobileMenuOpen(false)}>
                  Sign In
                </Link>
                <Link href="/register">
                  <Button className="rounded-full">
                    Get Started
                    <ChevronRight className="ml-1 size-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </header>
      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-20 md:py-32 lg:py-40 overflow-hidden">
          <div className="landing-container px-4 md:px-6 relative">
            <div className="absolute inset-0 -z-10 h-full w-full bg-[linear-gradient(to_right,rgba(209,250,229,0.7)_1px,transparent_1px),linear-gradient(to_bottom,rgba(209,250,229,0.7)_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,rgba(6,78,59,0.5)_1px,transparent_1px),linear-gradient(to_bottom,rgba(6,78,59,0.5)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_72%,transparent_110%)]"></div>
            <div className="absolute -top-40 left-1/2 -translate-x-1/2 -z-10 h-[560px] w-[560px] rounded-full bg-gradient-to-br from-emerald-300/28 via-emerald-100/18 to-transparent blur-3xl"></div>
            <motion.div
              variants={heroVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.7 }}
              className="text-center max-w-3xl mx-auto mb-12"
            >
              <Badge className="fw-pill mb-4 rounded-full px-4 py-1.5 text-sm font-medium" variant="secondary">
                Nalytiq Rwanda's Official Data Platform
              </Badge>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-emerald-800 via-primary to-foreground dark:from-emerald-200 dark:via-emerald-100 dark:to-foreground">
                Empowering Africa with AI-Powered Data Insights
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                The all-in-one platform for data scientists, statisticians, policymakers, and public servants to analyze, visualize, and report on national datasets.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register">
                  <Button size="lg" className="rounded-full h-12 px-8 text-base bg-gradient-to-r from-primary via-emerald-600 to-emerald-700 text-primary-foreground shadow-md shadow-emerald-900/10 hover:opacity-95">
                    Get Started
                    <ArrowRight className="ml-2 size-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline" className="rounded-full h-12 px-8 text-base bg-white/60 dark:bg-black/10 backdrop-blur border-border/70 hover:bg-white/75 dark:hover:bg-black/20">
                    Sign In
                  </Button>
                </Link>
              </div>
              <div className="flex items-center justify-center gap-4 mt-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Check className="size-4 text-primary" />
                  <span>No credit card</span>
                </div>
                <div className="flex items-center gap-1">
                  <Check className="size-4 text-primary" />
                  <span>Government-backed</span>
                </div>
                <div className="flex items-center gap-1">
                  <Check className="size-4 text-primary" />
                  <span>Secure & Private</span>
                </div>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.7 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="relative mx-auto max-w-5xl"
            >
              <div className="fw-surface overflow-hidden">
                <Image
                  src="/hero.png"
                  width={1280}
                  height={720}
                  alt="Nalytiq platform hero image"
                  className="w-full h-auto"
                  priority
                />
                <div className="absolute inset-0 rounded-xl ring-1 ring-inset ring-black/10 dark:ring-white/10"></div>
              </div>
              <div className="absolute -bottom-10 -right-10 -z-10 h-[320px] w-[320px] rounded-full bg-gradient-to-br from-emerald-400/18 to-emerald-200/12 blur-3xl opacity-70"></div>
              <div className="absolute -top-10 -left-10 -z-10 h-[320px] w-[320px] rounded-full bg-gradient-to-br from-emerald-200/14 to-primary/14 blur-3xl opacity-70"></div>
            </motion.div>
        </div>
      </section>
        {/* Features Section */}
        <section id="features" className="w-full py-20 md:py-32">
        <div className="landing-container px-4 md:px-6">
            <motion.div
              variants={featuresVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="flex flex-col items-center justify-center space-y-4 text-center mb-12"
            >
              <Badge className="fw-pill rounded-full px-4 py-1.5 text-sm font-medium" variant="secondary">
                Features
              </Badge>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Powerful Tools for Data-Driven Africa</h2>
              <p className="max-w-[800px] text-muted-foreground md:text-lg">
                Our platform combines cutting-edge AI with robust statistical tools to transform how Africa uses data.
              </p>
            </motion.div>
            <motion.div
              variants={featuresVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
            >
              {features.map((feature, i) => (
                <motion.div key={i} variants={item}>
                  <Card className="fw-surface h-full overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-emerald-900/10">
                    <CardContent className="p-6 flex flex-col h-full">
                      <div className="size-10 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary mb-4">
                        {feature.icon}
            </div>
                      <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                      <p className="text-muted-foreground">{feature.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
        {/* How It Works Section */}
        <section id="how-it-works" className="w-full py-20 md:py-32 bg-emerald-50/35 dark:bg-emerald-950/10 relative overflow-hidden">
          <div className="absolute inset-0 -z-10 h-full w-full bg-[linear-gradient(to_right,#d1fae5_1px,transparent_1px),linear-gradient(to_bottom,#d1fae5_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#064e3b_1px,transparent_1px),linear-gradient(to_bottom,#064e3b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,#000_42%,transparent_100%)]"></div>
          <div className="landing-container px-4 md:px-6 relative">
            <motion.div
              variants={howItWorksVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="flex flex-col items-center justify-center space-y-4 text-center mb-16"
            >
              <Badge className="fw-pill rounded-full px-4 py-1.5 text-sm font-medium" variant="secondary">
                How It Works
              </Badge>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Simple, Powerful Workflow</h2>
              <p className="max-w-[800px] text-muted-foreground md:text-lg">
                Our platform streamlines the entire data lifecycle from upload to insight.
              </p>
            </motion.div>
            <motion.div
              variants={howItWorksVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="grid md:grid-cols-3 gap-8 md:gap-12 relative"
            >
              <div className="hidden md:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-border to-transparent -translate-y-1/2 z-0"></div>
              {steps.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="relative z-10 flex flex-col items-center text-center space-y-4"
                >
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary via-emerald-600 to-emerald-700 text-primary-foreground text-xl font-bold shadow-lg shadow-emerald-900/10">
                    {step.step}
                  </div>
                  <h3 className="text-xl font-bold">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </motion.div>
            ))}
            </motion.div>
          </div>
        </section>
        {/* FAQ Section */}
        <section id="faq" className="w-full py-20 md:py-32">
          <div className="landing-container px-4 md:px-6">
            <motion.div
              variants={faqVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="flex flex-col items-center justify-center space-y-4 text-center mb-12"
            >
              <Badge className="fw-pill rounded-full px-4 py-1.5 text-sm font-medium" variant="secondary">
                FAQ
              </Badge>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Frequently Asked Questions</h2>
              <p className="max-w-[800px] text-muted-foreground md:text-lg">
                Find answers to common questions about our platform.
              </p>
            </motion.div>
            <motion.div
              variants={faqVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="mx-auto max-w-3xl"
            >
              <Accordion type="single" collapsible className="w-full">
                {faqs.map((faq, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: i * 0.05 }}
                  >
                    <AccordionItem value={`item-${i}`} className="border-b border-border/40 py-2">
                      <AccordionTrigger className="text-left font-medium hover:no-underline">
                        {faq.question}
                      </AccordionTrigger>
                      <AccordionContent className="text-muted-foreground">{faq.answer}</AccordionContent>
                    </AccordionItem>
                  </motion.div>
                ))}
              </Accordion>
            </motion.div>
        </div>
      </section>
      {/* CTA Section */}
        <section className="w-full py-20 md:py-32 bg-gradient-to-br from-primary via-emerald-600 to-emerald-800 text-primary-foreground relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#ffffff10_1px,transparent_1px),linear-gradient(to_bottom,#ffffff10_1px,transparent_1px)] bg-[size:4rem_4rem]"></div>
          <div className="absolute -top-24 -left-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
          <div className="landing-container px-4 md:px-6 relative">
            <motion.div
              variants={ctaVariant}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, amount: 0.3 }}
              className="fw-surface-inverse flex flex-col items-center justify-center space-y-6 text-center p-10 md:p-12"
            >
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight">
                Ready to Transform Your Data?
              </h2>
              <p className="mx-auto max-w-[700px] text-primary-foreground/80 md:text-xl">
                Join leading institutions already using our platform to drive data-informed decisions.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 mt-4">
              <Link href="/register">
                  <Button size="lg" variant="secondary" className="rounded-full h-12 px-8 text-base">
                    Get Started
                    <ArrowRight className="ml-2 size-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                    className="rounded-full h-12 px-8 text-base bg-transparent border-white text-white hover:bg-white/10"
                >
                  Sign In
                </Button>
              </Link>
            </div>
              <p className="text-sm text-primary-foreground/80 mt-4">
                No credit card required. Government-backed. Secure & Private.
              </p>
            </motion.div>
        </div>
      </section>
      </main>
      <footer className="w-full border-t bg-background/95 backdrop-blur-sm">
        <div className="landing-container flex flex-col gap-8 px-4 py-10 md:px-6 lg:py-16">
          <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2 font-bold">
                <div className="size-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-primary-foreground">
                  N
                </div>
                <span>Nalytiq</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Headquarters
                <br />
                Kigali, Rwanda
              </p>
              <div className="flex gap-4">
                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="size-5"
                  >
                    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
                  </svg>
                  <span className="sr-only">Facebook</span>
                </Link>
                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="size-5"
                  >
                    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                  </svg>
                  <span className="sr-only">Twitter</span>
                </Link>
                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="size-5"
                  >
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                    <rect width="4" height="12" x="2" y="9"></rect>
                    <circle cx="4" cy="4" r="2"></circle>
                  </svg>
                  <span className="sr-only">LinkedIn</span>
                </Link>
              </div>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-bold">Platform</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#how-it-works" className="text-muted-foreground hover:text-foreground transition-colors">
                    How It Works
                  </Link>
                </li>
                <li>
                  <Link href="#faq" className="text-muted-foreground hover:text-foreground transition-colors">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-bold">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    API
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    Support
                  </Link>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="text-sm font-bold">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                    Data Policy
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="w-full max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between border-t border-border/40 pt-8 mt-8 gap-2">
            <div className="flex-1 flex justify-start">
              <p className="text-xs text-muted-foreground">&copy; {new Date().getFullYear()} Nalytiq. All rights reserved.</p>
            </div>
            <div className="flex-1 flex justify-center text-center">
              <p className="text-xs text-muted-foreground">
                Nalytiq &nbsp;|&nbsp; created by <a href="https://chrismazii.online" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary">Chris Mazimpaka</a> &bull; matthew 5:16
              </p>
            </div>
            <div className="flex-1 flex justify-end gap-4">
              <Link href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Terms of Service
              </Link>
              <Link href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Data Policy
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
