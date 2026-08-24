import React from "react";
import { Link } from "react-router-dom";
import { Header } from "../components/Header";
import { SpectatorLogo } from "../components/SpectatorLogo";

export const LandingPage: React.FC = () => {
  return (
    <div className="bg-background text-on-background font-body-md antialiased min-h-screen flex flex-col selection:bg-primary-container selection:text-on-primary-container">
      <Header />

      <main className="flex-grow flex flex-col pt-24">
        {/* Hero Section */}
        <section className="flex flex-col items-center justify-center text-center px-margin-mobile md:px-margin-desktop py-24 md:py-32 max-w-container-max mx-auto w-full">
          <h1 className="font-display-lg-mobile text-display-lg-mobile md:font-display-lg md:text-display-lg text-on-surface max-w-4xl mb-6 leading-tight">
            Give it a subject,
            <br className="hidden md:block" /> get back a report.
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-12">
            Spectator is your AI research assistant that investigates topics
            deeply and delivers polished dossiers while you focus on high-level
            thinking.
          </p>
          <Link
            to="/signup"
            className="bg-primary-container text-on-primary-container font-label-sm text-label-sm px-8 py-4 rounded transition-opacity duration-200 hover:opacity-90 flex items-center gap-2"
          >
            Start researching
            <span className="material-symbols-outlined text-[18px]">
              arrow_forward
            </span>
          </Link>
        </section>

        {/* Process Section */}
        <section className="px-margin-mobile md:px-margin-desktop py-24 bg-surface-container-lowest border-t border-outline-variant w-full">
          <div className="max-w-container-max mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-gutter relative">
              {/* Connecting Line (Desktop) */}
              <div className="hidden md:block absolute top-12 left-[15%] right-[15%] h-px bg-outline-variant z-0"></div>

              {/* Step 1 */}
              <div className="flex flex-col items-center text-center relative z-10">
                <div className="w-24 h-24 rounded-full bg-surface border border-outline-variant flex items-center justify-center mb-6 text-on-surface-variant">
                  <span className="material-symbols-outlined text-4xl">
                    edit_note
                  </span>
                </div>
                <span className="font-label-sm text-label-sm text-primary mb-2">
                  01
                </span>
                <h3 className="font-headline-md text-headline-md text-on-surface mb-3">
                  Ask
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Provide a topic, question, or specific area of interest.
                </p>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col items-center text-center relative z-10">
                <div className="w-24 h-24 rounded-full bg-surface border border-outline-variant flex items-center justify-center mb-6 text-on-surface-variant">
                  <span className="material-symbols-outlined text-4xl">
                    search
                  </span>
                </div>
                <span className="font-label-sm text-label-sm text-primary mb-2">
                  02
                </span>
                <h3 className="font-headline-md text-headline-md text-on-surface mb-3">
                  Researches
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Spectator autonomously gathers, synthesizes, and
                  cross-references data.
                </p>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col items-center text-center relative z-10">
                <div className="w-24 h-24 rounded-full bg-surface border border-outline-variant flex items-center justify-center mb-6 text-on-surface-variant">
                  <span className="material-symbols-outlined text-4xl">
                    article
                  </span>
                </div>
                <span className="font-label-sm text-label-sm text-primary mb-2">
                  03
                </span>
                <h3 className="font-headline-md text-headline-md text-on-surface mb-3">
                  Report
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Receive a structured, comprehensive dossier ready for review.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};
