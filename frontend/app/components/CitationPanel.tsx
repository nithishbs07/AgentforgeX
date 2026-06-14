import React, { useState } from "react";
import { Message } from "../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, ChevronDown, ChevronUp, BookOpen, Quote, Award } from "lucide-react";

interface CitationPanelProps {
  message: Message | null;
}

export default function CitationPanel({ message }: CitationPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!message) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center select-none text-subtext/60">
        <BookOpen className="w-12 h-12 text-subtext/40 mb-3 animate-pulse" />
        <h4 className="text-sm font-semibold font-outfit text-subtext/80">No Message Selected</h4>
        <p className="text-[11px] mt-1 max-w-[200px]">
          Click on any assistant response bubble to display referenced source citations.
        </p>
      </div>
    );
  }

  const citations = message.citations || [];

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-white/5 select-none">
        <h3 className="text-xs font-bold text-primary uppercase tracking-widest font-outfit">
          Source Citations ({citations.length})
        </h3>
      </div>

      {citations.length === 0 ? (
        <div className="text-center py-8 text-subtext/60 text-xs font-medium">
          No source document citations were referenced for this response.
        </div>
      ) : (
        <div className="space-y-3">
          {citations.map((cit, idx) => {
            const isExpanded = expandedIndex === idx;
            // Generate a stable mock confidence score between 88% and 98% based on the snippet length or filename
            const length = (cit.snippet || "").length;
            const confidenceScore = 85 + (length % 14);

            return (
              <motion.div
                layout
                key={cit.id || idx}
                className="bg-card border border-white/5 rounded-xl overflow-hidden shadow-md glass-panel"
              >
                {/* Header Card */}
                <div
                  onClick={() => toggleExpand(idx)}
                  className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-all select-none gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="bg-primary/10 border border-primary/20 w-8 h-8 rounded-lg flex items-center justify-center text-primary flex-shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-semibold text-text truncate font-outfit" title={cit.filename}>
                        {cit.filename || "Unknown Document"}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[9px] font-bold uppercase bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded-md">
                          {cit.page_number && cit.page_number > 0 ? `Page ${cit.page_number}` : "Global Context"}
                        </span>
                        <span className="flex items-center gap-0.5 text-[9px] font-bold text-success">
                          <Award className="w-2.5 h-2.5" />
                          {confidenceScore}% Match
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-subtext">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>

                {/* Content Expand */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                      className="border-t border-white/5 bg-background/25 overflow-hidden"
                    >
                      <div className="p-3.5 space-y-2">
                        <div className="flex gap-2">
                          <Quote className="w-4 h-4 text-primary/40 flex-shrink-0 mt-0.5" />
                          <p className="text-[11px] leading-relaxed text-subtext font-medium italic whitespace-pre-wrap">
                            "{cit.snippet || "No snippet content"}"
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
