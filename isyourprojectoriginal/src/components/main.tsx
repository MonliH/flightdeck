"use client";

import { useState, FormEvent } from "react";
import dynamic from "next/dynamic";
import { Project, SimilarityResult } from "@/lib/types";
import Link from "next/link";
import Markdown from "react-markdown";
import { ArrowBigRight } from "lucide-react";

const CARD_COLORS = ["bg-pink-200", "bg-blue-200", "bg-purple-200"];

function formatTextToStyledSpans(
  text: string,
  color: string,
  url: string | null = null
): string {
  // Split into lines
  const lines = text.split("\n").filter((line) => line.trim());
  return lines
    .map((line) => {
      // Match any bold text patterns in the line
      let formattedLine = line;
      const boldPattern = /\*\*([^*]+)\*\*/g;

      formattedLine = formattedLine.replace(boldPattern, (_, boldText) => {
        return `<a ${
          url ? 'href="' + url + '"' : ""
        } style="background-color: ${color}" target="_blank" class="font-bold text-black py-0.5 px-1 rounded-sm">${boldText}</a>`;
      });

      // If the line contains any formatted content, wrap the remaining text in spans
      if (formattedLine !== line) {
        // Split the line into parts that are either bold or not
        const parts = formattedLine.split(/(<a.*?<\/a>)/g);

        // Wrap non-bold parts in spans
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

const baseUrl = process.env.BASE_URL;

export default function Main() {
  const [input, setInput] = useState<string>("");
  const [results, setResults] = useState<SimilarityResult[]>([]);
  const [error, setError] = useState<string>("");
  const [submitted, setSubmitted] = useState<boolean>(false);

  const [whatTheyDid, setWhatTheyDid] = useState<string[]>([]);
  const [howTheyWon, setHowTheyWon] = useState<string[]>([]);

  const [suggestion, setSuggestions] = useState<string[]>([]);
  const [activeSuggestion, setActiveSuggestion] = useState<number>(0);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSubmitted(true);

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
    }

    if (data === null) {
      return;
    }

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
    }

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
          names: data.map(([_, project]) => project.title),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch how they won");
      }

      const d = await response.json();

      setHowTheyWon(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  const handleSuggestions = async () => {
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
                  {submission.awards[0].split("sponsored by")[0]}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Link>
    </div>
  );

  return (
    <div className="bg-[#FFF7ED] py-12 px-12 h-screen w-screen">
      <div className="space-y-8 h-full">
        <a className="absolute top-4 right-4 bold font-[Yrsa]" href="/">Project Name</a>
        <img className="absolute top-16 left-20 w-40 z-0" src="/sun.png"></img>
        <img className="absolute bottom-20 left-28 w-40 z-0" src="/heart.png"></img>
        <img className="absolute bottom-16 right-24 w-40 z-0" src="/computer.png"></img>
        <div className="flex items-center gap-4 justify-center">
          {!submitted ? (
            <h1
              className={`text-7xl font-bold text-[#A5B5FB] mt-36`}
              style={{
                WebkitTextStroke: "1px #000",
              }}
            >
              Are u a fraud?
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
              className="mx-auto block text-slate-500 border-2 border-orange-300 bg-white py-1 px-4 rounded-sm hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Start
            </button>
          </form></div>
        )}

        {error && (
          <div className="p-4 bg-red-100 text-red-600 rounded-2xl text-center">
            {error}
          </div>
        )}

        {
          <div
            className="flex-row w-full content-end h-full gap-8"
            style={{
              opacity: results.length ? 1 : 0,
              display: results.length ? "flex" : "none",
            }}
          >
            <div className="w-5/12 shrink-0 ml-72">
              {suggestion.length == 0 ? (
                <>
                  <h2 className="text-lg text-[#48566A] mb-2">
                    Let me first assess what they did..
                  </h2>
                  <div
                    className="p-3 bg-white rounded-md text-lg py-5 flex flex-col gap-1"
                    style={{
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
                  <h2 className="text-lg text-[#48566A] mt-5 mb-2">
                    Let me assess why they won...
                  </h2>
                  <div className="p-3 bg-white rounded-md text-lg py-5 flex flex-col gap-1">
                    {howTheyWon.map((text, index) => (
                      <div
                        key={index}
                        dangerouslySetInnerHTML={{
                          __html: formatTextToStyledSpans(
                            text,
                            "#EFD4FF",
                            null
                          ),
                        }}
                      />
                    ))}
                  </div>
                  {howTheyWon.length > 0 && (
                    <button
                      onClick={handleSuggestions}
                      className="mx-auto block text-slate-500 border-2 border-[#FFE6C6] bg-white py-1 px-4 rounded-sm hover:bg-orange-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-3"
                    >
                      Start the Arena
                    </button>
                  )}
                </>
              ) : (
                <>
                  <h2 className="text-lg text-[#48566A] mb-2">
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
              <h2 className="text-lg text-[#48566A]">Banger Projects</h2>
              {results.map(([score, project], index) => (
                <ProjectCard
                  key={index}
                  score={score}
                  project={project}
                  color={CARD_COLORS[index % CARD_COLORS.length]}
                />
              ))}
            </div>
          </div>
        }
      </div>
    </div>
  );
}
