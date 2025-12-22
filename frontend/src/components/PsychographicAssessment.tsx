import React, { useState, useEffect } from 'react';

interface Question {
  id: number;
  question_text: string;
  category: string;
  options: Option[];
}

interface Option {
  id: number;
  option_text: string;
  order: number;
}

interface AssessmentResult {
  primary_type: string;
  primary_type_label: string;
  primary_score: number;
  description: string;
  play_style_summary: string;
  conversation_guidance: string;
  preference_breakdown: Record<string, number>;
}

export const PsychographicAssessment: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch questionnaire on mount
  useEffect(() => {
    const fetchQuestionnaire = async () => {
      try {
        const response = await fetch('/api/profiles/questionnaire');
        const data = await response.json();
        setQuestions(data.questions);
        setLoading(false);
      } catch (err) {
        setError('Failed to load questionnaire');
        setLoading(false);
      }
    };

    fetchQuestionnaire();
  }, []);

  // Handle answer selection
  const handleAnswer = (questionId: number, optionId: number) => {
    setAnswers({
      ...answers,
      [questionId]: optionId,
    });
  };

  // Submit assessment
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all questions answered
    if (Object.keys(answers).length !== questions.length) {
      setError('Please answer all questions');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const token = localStorage.getItem('token'); // Adjust based on auth
      const response = await fetch('/api/profiles/assess', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          answers: Object.entries(answers).map(([questionId, optionId]) => ({
            question_id: parseInt(questionId),
            selected_option_id: optionId,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit assessment');
      }

      const resultData = await response.json();
      setResult(resultData);
    } catch (err) {
      setError('Failed to submit assessment');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading questionnaire...</div>;
  }

  if (result) {
    return <ResultDisplay result={result} />;
  }

  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded-lg shadow">
      <h1 className="text-3xl font-bold mb-2">Player Archetype Assessment</h1>
      <p className="text-gray-600 mb-8">
        Discover your Magic: The Gathering player archetype. This quick assessment helps Melvin understand your playstyle.
      </p>

      <form onSubmit={handleSubmit}>
        {questions.map((question, index) => (
          <div key={question.id} className="mb-8 pb-8 border-b">
            <h2 className="text-lg font-semibold mb-4">
              Question {index + 1} of {questions.length}
            </h2>
            <p className="text-lg mb-6 font-medium">{question.question_text}</p>

            <div className="space-y-3">
              {question.options.map((option) => (
                <label
                  key={option.id}
                  className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition"
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    value={option.id}
                    checked={answers[question.id] === option.id}
                    onChange={() => handleAnswer(question.id, option.id)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="ml-3 text-base">{option.option_text}</span>
                </label>
              ))}
            </div>

            {/* Progress indicator */}
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{
                  width: `${((index + (answers[question.id] ? 1 : 0)) / questions.length) * 100}%`,
                }}
              />
            </div>
          </div>
        ))}

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || Object.keys(answers).length !== questions.length}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {submitting ? 'Analyzing...' : 'Get My Archetype'}
        </button>
      </form>
    </div>
  );
};

interface ResultDisplayProps {
  result: AssessmentResult;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  return (
    <div className="max-w-2xl mx-auto p-8 bg-white rounded-lg shadow">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">
          {result.primary_type_label}
        </h1>
        <div className="w-full bg-gray-200 rounded-full h-3 max-w-xs mx-auto">
          <div
            className="bg-blue-600 h-3 rounded-full"
            style={{ width: `${result.primary_score * 100}%` }}
          />
        </div>
        <p className="text-gray-600 mt-2">
          {Math.round(result.primary_score * 100)}% match
        </p>
      </div>

      <div className="mb-8 p-6 bg-blue-50 rounded-lg">
        <h2 className="text-xl font-semibold mb-3">Who You Are</h2>
        <p className="text-gray-700">{result.description}</p>
      </div>

      <div className="mb-8 p-6 bg-green-50 rounded-lg">
        <h2 className="text-xl font-semibold mb-3">Your Play Style</h2>
        <p className="text-gray-700">{result.play_style_summary}</p>
      </div>

      <div className="mb-8 p-6 bg-purple-50 rounded-lg">
        <h2 className="text-xl font-semibold mb-3">How Melvin Will Help</h2>
        <p className="text-gray-700">{result.conversation_guidance}</p>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Your Preferences</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(result.preference_breakdown).map(([key, value]) => (
            <div key={key} className="p-4 border rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium capitalize">
                  {key === 'big_plays'
                    ? 'Big Plays'
                    : key.charAt(0).toUpperCase() + key.slice(1)}
                </span>
                <span className="text-gray-600">
                  {Math.round(value * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${value * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => window.location.reload()}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition"
        >
          Retake Assessment
        </button>
        <button
          onClick={() => window.history.back()}
          className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-4 rounded-lg transition"
        >
          Continue to Game
        </button>
      </div>
    </div>
  );
};

export default PsychographicAssessment;
