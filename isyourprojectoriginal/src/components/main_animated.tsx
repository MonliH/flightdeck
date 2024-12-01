"use client";

/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @next/next/no-html-link-for-pages */

import { useState, FormEvent } from "react";
import { Project, SimilarityResult } from "@/lib/types";
import Link from "next/link";
import Markdown from "react-markdown";
import { Loader2 } from "lucide-react";

const CARD_COLORS = ["bg-pink-200", "bg-blue-200", "bg-purple-200"];

function formatTextToStyledSpans(
  text: string,
  color: string,
  url: string | null = null
): string {
  const lines = text.split("\n").filter((line) => line.trim());
  return lines
    .map((line) => {
      let formattedLine = line;
      const boldPattern = /\*\*([^*]+)\*\*/g;

      formattedLine = formattedLine.replace(boldPattern, (_, boldText) => {
        return `<a ${
          url ? 'href="' + url + '"' : ""
        } style="background-color: ${color}" target="_blank" class="font-bold text-black py-0.5 px-1 rounded-sm">${boldText}</a>`;
      });

      if (formattedLine !== line) {
        const parts = formattedLine.split(/(<a.*?<\/a>)/g);
        formattedLine = parts
          .map((part) => {
            if (part.startsWith("<a")) {
              return part;
            }
            return part.trim() ? `<span>${part}</span>` : part;
          })
          .join("");
      }

      return formattedLine;
    })
    .join("\n");
}

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL;

// Loading skeleton component for project cards
const ProjectCardSkeleton = () => (
  <div className="rounded-lg overflow-hidden shadow-sm bg-white h-48 w-64 animate-pulse">
    <div className="w-full h-3/5 bg-gray-200" />
    <div className="p-4">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
      <div className="h-3 bg-gray-200 rounded w-1/2" />
    </div>
  </div>
);

const LOADING_MESSAGES = [
  { text: "Extracting key insights from winning projects...", duration: 2000 },
  { text: "Sampling from models...", duration: 6000 },
  { text: "Running embedding similarity...", duration: 10000 },
];

export default function Main() {
  const [input, setInput] = useState<string>("");
  const [results, setResults] = useState<SimilarityResult[]>([]);
  const [error, setError] = useState<string>("");
  const [submitted, setSubmitted] = useState<boolean>(false);

  const [whatTheyDid, setWhatTheyDid] = useState<string[]>([]);
  const [howTheyWon, setHowTheyWon] = useState<string[]>([]);
  const [suggestion, setSuggestions] = useState<string[]>([]);
  const [activeSuggestion, _setActiveSuggestion] = useState<number>(0);

  // New loading states
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [isLoadingWhatTheyDid, setIsLoadingWhatTheyDid] = useState(false);
  const [isLoadingHowTheyWon, setIsLoadingHowTheyWon] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);

  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(-1);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSubmitted(true);
    setIsLoadingResults(true);

    let data: SimilarityResult[] | null = null;
    try {
      const response = await fetch(`${baseUrl}/similar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document_or_link: input,
          k: 3,
          filter: { award: "big" },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch similar projects");
      }

      data = (await response.json()) as SimilarityResult[];
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoadingResults(false);
    }

    if (data === null) {
      return;
    }

    setIsLoadingWhatTheyDid(true);
    try {
      const response = await fetch(`${baseUrl}/what-they-did`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          documents: data.map(
            ([, project]) => project.parsed_content.description_markdown
          ),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch what they did");
      }

      const d: string[] = await response.json();
      setWhatTheyDid(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoadingWhatTheyDid(false);
    }

    setIsLoadingHowTheyWon(true);
    try {
      const response = await fetch(`${baseUrl}/how-they-won`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          documents: data.map(
            ([, project]) => project.parsed_content.description_markdown
          ),
          prizes: data.map(([, project]) =>
            project.parsed_content.submissions
              .map((submission) => submission.awards.join(", "))
              .join(", ")
          ),
          names: data.map(([_a, project]) => project.title),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch how they won");
      }

      const d = await response.json();
      setHowTheyWon(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoadingHowTheyWon(false);
    }
  };

  const startProgressAnimation = () => {
    setCompletedSteps([]);
    setCurrentStep(0);

    let stepIndex = 0;
    const processNextStep = () => {
      if (stepIndex < LOADING_MESSAGES.length) {
        setCurrentStep(stepIndex);
        setTimeout(() => {
          setCompletedSteps((prev) => [...prev, stepIndex]);
          stepIndex++;
          processNextStep();
        }, LOADING_MESSAGES[stepIndex].duration);
      }
    };

    processNextStep();
  };

  const handleSuggestions = async () => {
    setIsLoadingSuggestions(true);
    startProgressAnimation();

    try {
      const response = await fetch(`${baseUrl}/arena`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_doc: input,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch suggestions");
      }

      const d: { similar_projects: Project[]; sorted_suggestions: string[] } =
        await response.json();

      setSuggestions(d.sorted_suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoadingSuggestions(false);
      setTimeout(() => {
        setCurrentStep(-1);
        setCompletedSteps([]);
      }, 0); // Give a small delay after loading completes
    }
  };

  const ProjectCard = ({
    score,
    project,
    color,
  }: {
    score: number;
    project: Project;
    color: string;
  }) => (
    <div className="rounded-lg overflow-hidden shadow-sm bg-white hover:shadow-lg transition-shadow h-48 w-64 flex flex-col">
      <Link
        href={project.project_url}
        target="_blank"
        className="h-full flex flex-col"
      >
        <div className="w-full h-3/5 relative overflow-hidden">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `url(${project.thumbnail_url.replace(
                "medium.jpeg",
                "original.jpeg"
              )})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />
        </div>
        <div className="p-4 flex-grow">
          <div className="flex justify-between items-start">
            <h3 className="text-md leading-tight font-bold text-gray-900">
              {project.title}
            </h3>
            <div className="text-right">
              <div className="text-xs font-medium text-gray-900">Prize</div>
              {project.parsed_content.submissions.map((submission, idx) => (
                <div
                  key={idx}
                  className="text-xs text-gray-600 text-right max-w-32"
                >
                  {submission.awards[0].split("sponsored by")[0].split(" &")[0].slice(0, 55)}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );

  return (
    <div className="py-12 px-12 h-screen w-screen overflow-hidden" style={{
        backgroundImage: 'url("/bg_pattern.jpg")',
        backgroundRepeat: "repeat"
    }}>
      <div className="space-y-8 h-full">
        <a className={`absolute top-4 right-4`} href="/">
          <img
            src="/logo.png"
            className="w-10 h-10 rounded-md border-black border"
          ></img>
        </a>
        <img
          className="absolute top-[7.25rem] left-[7.8rem] w-16 z-10"
          src="/sun_face.png"
        ></img>
        <img
          className="absolute top-16 left-20 w-40 z-0 animate-spin"
          src="/sun.png"
          style={{
            animation: submitted ? "none" : "spin 20s linear infinite",
          }}
        ></img>
        <img
          className="absolute bottom-20 left-28 w-40 z-0"
          src="/heart.png"
        ></img>
        <img
          className="absolute bottom-16 right-24 w-40 z-0"
          src="/computer.png"
        ></img>

        <div className="flex items-center gap-4 justify-center">
          {!submitted ? (
            <h1
              className={`text-9xl italic font-bold text-[#A5B5FB] mt-36`}
              style={{
                WebkitTextStroke: "3px #000",
                paintOrder: "stroke fill",
                fontStyle: "italic",
                fontFamily: "Yrsa, serif",
              }}
            >
              Flightdeck
            </h1>
          ) : null}
        </div>

        {!submitted && (
          <div className="flex flex-col items-center mt-16">
            <form onSubmit={handleSubmit} className="space-y-4 w-1/2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Enter your Devpost submission link or a description of your project..."
                className="w-full h-32 p-4 rounded-2xl border-2 focus:border-blue-400 focus:ring-0 text-slate-600 placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={isLoadingResults}
                className="mx-auto block text-slate-500 border-2 border-orange-300 bg-white py-1 px-4 rounded-sm hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoadingResults ? (
                  <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                ) : null}
                Start
              </button>
            </form>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-100 text-red-600 rounded-2xl text-center">
            {error}
          </div>
        )}

        <div
          className="flex-row w-full content-end h-full gap-8 transition-opacity duration-500 ease-in-out"
          style={{
            opacity: results.length || isLoadingResults ? 1 : 0,
            display: results.length || isLoadingResults ? "flex" : "none",
          }}
        >
          <div className="w-5/12 shrink-0 ml-72">
            {suggestion.length == 0 ? (
              <>
                <h2 className="text-lg text-[#48566A] mb-2 flex items-center gap-2">
                  Let me first assess what they did..
                  {isLoadingWhatTheyDid && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                </h2>
                <div
                  className="p-3 bg-white rounded-md text-lg py-5 flex flex-col gap-1 transition-opacity duration-300"
                  style={{
                    opacity: isLoadingWhatTheyDid ? 0.5 : 1,
                    boxShadow: `0px 0px 2.7px -13px rgba(0, 0, 0, 0.022),
                               0px 0px 6.9px -13px rgba(0, 0, 0, 0.031),
                               0px 0px 14.2px -13px rgba(0, 0, 0, 0.039),
                               0px 0px 29.2px -13px rgba(0, 0, 0, 0.048),
                               0px 0px 80px -13px rgba(0, 0, 0, 0.07)`,
                  }}
                >
                  {whatTheyDid.map((text, index) => (
                    <div
                      key={index}
                      dangerouslySetInnerHTML={{
                        __html: formatTextToStyledSpans(
                          text,
                          "#FFDEB3",
                          results[index][1].project_url
                        ),
                      }}
                    />
                  ))}
                </div>
                <h2 className="text-lg text-[#48566A] mt-5 mb-2 flex items-center gap-2">
                  Let me assess why they won...
                  {isLoadingHowTheyWon && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                </h2>
                <div
                  className="p-3 bg-white rounded-md text-lg py-5 flex flex-col gap-1 transition-opacity duration-300"
                  style={{ opacity: isLoadingHowTheyWon ? 0.5 : 1 }}
                >
                  {howTheyWon.map((text, index) => (
                    <div
                      key={index}
                      dangerouslySetInnerHTML={{
                        __html: formatTextToStyledSpans(text, "#EFD4FF", null),
                      }}
                    />
                  ))}
                </div>
                {howTheyWon.length > 0 && (
                  <>
                    <button
                      onClick={handleSuggestions}
                      disabled={isLoadingSuggestions}
                      className="mx-auto block text-slate-500 border-2 border-[#FFE6C6] bg-white py-1 px-4 rounded-sm hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-3"
                    >
                      {isLoadingSuggestions ? (
                        <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                      ) : null}
                      Start the Arena
                    </button>
                    {isLoadingSuggestions && (
                      <div className="max-w-md mx-auto mt-10">
                        <div className="space-y-2">
                          {LOADING_MESSAGES.map((step, index) => (
                            <div
                              key={index}
                              className={`flex items-center gap-3 transition-colors duration-300 ${
                                currentStep === index
                                  ? "text-blue-500"
                                  : completedSteps.includes(index)
                                  ? "text-green-500"
                                  : "text-gray-400"
                              }`}
                            >
                              <div className="w-5 h-5 flex-shrink-0">
                                {completedSteps.includes(index) ? (
                                  <div
                                    className={`w-2 h-2 rounded-full mx-auto my-1.5 bg-green-500 animate-pulse`}
                                  />
                                ) : (
                                  <div
                                    className={`w-2 h-2 rounded-full mx-auto my-1.5 ${
                                      currentStep === index
                                        ? "bg-blue-500 animate-pulse"
                                        : "bg-gray-300"
                                    }`}
                                  />
                                )}
                              </div>
                              <span
                                className={`text-sm ${
                                  currentStep === index
                                    ? "font-medium"
                                    : completedSteps.includes(index)
                                    ? "font-medium"
                                    : "text-gray-400"
                                }`}
                              >
                                {step.text}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </>
            ) : (
              <>
                <h2 className="text-lg text-[#48566A] -mt-14 mb-2">
                  The winning writeup out of <b>10 ideas</b> is...
                </h2>
                <div className="p-3 h-[700px] bg-white rounded-md text-lg py-5 flex flex-col gap-1 overflow-scroll">
                  <Markdown className="markdown">
                    {suggestion[activeSuggestion]}
                  </Markdown>
                </div>
              </>
            )}
          </div>
          <div className="h-full flex gap-4 flex-col justify-end pb-16 ml-4 -mt-14">
            <h2 className="text-lg text-[#48566A]">Related Winners</h2>
            {isLoadingResults ? (
              <>
                <ProjectCardSkeleton />
                <ProjectCardSkeleton />
                <ProjectCardSkeleton />
              </>
            ) : (
              results.map(([score, project], index) => (
                <div
                  key={index}
                  className="transition-opacity duration-500 ease-in-out"
                  style={{
                    opacity: isLoadingWhatTheyDid ? 0.5 : 1,
                    animationDelay: `${index * 150}ms`,
                  }}
                >
                  <ProjectCard
                    score={score}
                    project={project}
                    color={CARD_COLORS[index % CARD_COLORS.length]}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
