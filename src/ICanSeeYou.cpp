/*********************************************************************
* Software License Agreement (BSD License)
*
*  Copyright (c) 2008, Willow Garage, Inc.
*  All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without
*  modification, are permitted provided that the following conditions
*  are met:
*
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above
*     copyright notice, this list of conditions and the following
*     disclaimer in the documentation and/or other materials provided
*     with the distribution.
*   * Neither the name of the Willow Garage nor the names of its
*     contributors may be used to endorse or promote products derived
*     from this software without specific prior written permission.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
*  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
*  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
*  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
*  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
*  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
*  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
*  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
*  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
*  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
*  POSSIBILITY OF SUCH DAMAGE.
*********************************************************************/

/* Author: Ioan Sucan */

#include "ompl/geometric/planners/rrt/ICanSeeYou.h"
#include <limits>
#include "ompl/base/goals/GoalSampleableRegion.h"
#include "ompl/tools/config/SelfConfig.h"
#include "ompl/base/goals/GoalRegion.h"
#include "ompl/base/goals/GoalState.h"

ompl::geometric::ICanSeeYou::ICanSeeYou(const base::SpaceInformationPtr &si, bool addIntermediateStates)
  : base::Planner(si, addIntermediateStates ? "ICanSeeYouintermediate" : "ICanSeeYou")
{
    specs_.approximateSolutions = true;
    specs_.directed = true;

    Planner::declareParam<double>("range", this, &ICanSeeYou::setRange, &ICanSeeYou::getRange, "0.:1.:10000.");
    Planner::declareParam<double>("goal_bias", this, &ICanSeeYou::setGoalBias, &ICanSeeYou::getGoalBias, "0.:.05:1.");
    Planner::declareParam<bool>("intermediate_states", this, &ICanSeeYou::setIntermediateStates, &ICanSeeYou::getIntermediateStates,
                                "0,1");

    addIntermediateStates_ = addIntermediateStates;
}

ompl::geometric::ICanSeeYou::~ICanSeeYou()
{
    freeMemory();
}

void ompl::geometric::ICanSeeYou::clear()
{
    Planner::clear();
    sampler_.reset();
    freeMemory();
    if (nn_)
        nn_->clear();
    lastGoalMotion_ = nullptr;
}

void ompl::geometric::ICanSeeYou::setup()
{
    Planner::setup();
    tools::SelfConfig sc(si_, getName());
    sc.configurePlannerRange(maxDistance_);

    if (!nn_)
        nn_.reset(tools::SelfConfig::getDefaultNearestNeighbors<Motion *>(this));
    nn_->setDistanceFunction([this](const Motion *a, const Motion *b) { return distanceFunction(a, b); });
}

void ompl::geometric::ICanSeeYou::freeMemory()
{
    if (nn_)
    {
        std::vector<Motion *> motions;
        nn_->list(motions);
        for (auto &motion : motions)
        {
            if (motion->state != nullptr)
                si_->freeState(motion->state);
            delete motion;
        }
    }
}

ompl::base::PlannerStatus ompl::geometric::ICanSeeYou::solve(const base::PlannerTerminationCondition &ptc)
{
    checkValidity();
    base::Goal *goal = pdef_->getGoal().get();
    //auto *goal_s = dynamic_cast<base::GoalSampleableRegion *>(goal);

    // Initialize the tree with the start states
    while (const base::State *st = pis_.nextStart())
    {
        auto *motion = new Motion(si_);
        si_->copyState(motion->state, st);
        nn_->add(motion);
    }

    if (nn_->size() == 0)
    {
        OMPL_ERROR("%s: There are no valid initial states!", getName().c_str());
        return base::PlannerStatus::INVALID_START;
    }

    if (!sampler_)
        sampler_ = si_->allocStateSampler();

    OMPL_INFORM("%s: Starting planning with %u states already in datastructure", getName().c_str(), nn_->size());

    Motion *solution = nullptr;
    Motion *approxsol = nullptr;
    double approxdif = std::numeric_limits<double>::infinity();
    auto *rmotion = new Motion(si_);
    base::State *rstate = rmotion->state;
    base::State *xstate = si_->allocState();

    // Declare and allocate sampled states
    std::vector<base::State*> sampledStates(4); // Updated: Allocate space for 4 sampled states
    for (auto &state : sampledStates)
    {
        state = si_->allocState();
    }

    std::vector<base::State*> straightLinePathStates;
    base::State *selectedRandomNode = nullptr;
    std::vector<std::pair<base::State*, double>> intermediateGoalList;

    while (!ptc)
    {
        // Sample a set of random states
        for (auto &state : sampledStates)
        {
            sampler_->sampleUniform(state);
        }

        // Check if a straight-line path exists from each sampled state to the goal
        straightLinePathStates.clear();
        for (auto &state : sampledStates)
        {
            if (si_->checkMotion(state, goal->as<base::GoalState>()->getState()))
            {
                straightLinePathStates.push_back(state);
            }
        }

        if (!straightLinePathStates.empty())
        {
            if (straightLinePathStates.size() == 1)
            {
                selectedRandomNode = straightLinePathStates[0];
                intermediateGoalList.emplace_back(selectedRandomNode, si_->distance(selectedRandomNode, goal->as<base::GoalState>()->getState()));
            }
            else
            {
                selectedRandomNode = *std::min_element(straightLinePathStates.begin(), straightLinePathStates.end(),
                                                       [&](base::State *a, base::State *b)
                                                       {
                                                           return si_->distance(a, goal->as<base::GoalState>()->getState()) < si_->distance(b, goal->as<base::GoalState>()->getState());
                                                       });
                for (auto *state : straightLinePathStates)
                {
                    intermediateGoalList.emplace_back(state, si_->distance(state, goal->as<base::GoalState>()->getState()));
                }
            }
        }
        else if (!intermediateGoalList.empty())
        {
            std::vector<base::State*> pathToIntermediateStates;
            for (auto &state : sampledStates)
            {
                for (auto &intermediateGoal : intermediateGoalList)
                {
                    if (si_->checkMotion(state, intermediateGoal.first))
                    {
                        pathToIntermediateStates.push_back(state);
                        break;
                    }
                }
            }

            if (!pathToIntermediateStates.empty())
            {
                if (pathToIntermediateStates.size() == 1)
                {
                    selectedRandomNode = pathToIntermediateStates[0];
                }
                else
                {
                    selectedRandomNode = *std::min_element(pathToIntermediateStates.begin(), pathToIntermediateStates.end(),
                                                           [&](base::State *a, base::State *b)
                                                           {
                                                               return si_->distance(a, goal->as<base::GoalState>()->getState()) < si_->distance(b, goal->as<base::GoalState>()->getState());
                                                           });
                }
            }
        }

        if (!selectedRandomNode)
        {
            selectedRandomNode = *std::min_element(sampledStates.begin(), sampledStates.end(),
                                                   [&](base::State *a, base::State *b)
                                                   {
                                                       return si_->distance(a, goal->as<base::GoalState>()->getState()) < si_->distance(b, goal->as<base::GoalState>()->getState());
                                                   });
        }

        base::State *dstate = selectedRandomNode;

        // Find closest state in the tree
        Motion *nmotion = nn_->nearest(rmotion);
        double d = si_->distance(nmotion->state, selectedRandomNode);
        if (d > maxDistance_)
        {
            si_->getStateSpace()->interpolate(nmotion->state, selectedRandomNode, maxDistance_ / d, xstate);
            dstate = xstate;
        }

        if (si_->checkMotion(nmotion->state, dstate))
        {
            if (addIntermediateStates_)
            {
                std::vector<base::State *> states;
                const unsigned int count = si_->getStateSpace()->validSegmentCount(nmotion->state, dstate);

                if (si_->getMotionStates(nmotion->state, dstate, states, count, true, true))
                    si_->freeState(states[0]);

                for (std::size_t i = 1; i < states.size(); ++i)
                {
                    auto *motion = new Motion;
                    motion->state = states[i];
                    motion->parent = nmotion;
                    nn_->add(motion);

                    nmotion = motion;
                }
            }
            else
            {
                auto *motion = new Motion(si_);
                si_->copyState(motion->state, dstate);
                motion->parent = nmotion;
                nn_->add(motion);

                nmotion = motion;
            }

            double dist = 0.0;
            bool sat = goal->isSatisfied(nmotion->state, &dist);
            if (sat)
            {
                approxdif = dist;
                solution = nmotion;
                break;
            }
            if (dist < approxdif)
            {
                approxdif = dist;
                approxsol = nmotion;
            }
        }

        // Free selected random node if not used
        if (dstate != rstate)
            si_->freeState(dstate);
    }

    // Free the sampled states
    for (auto &state : sampledStates)
    {
        if (state != selectedRandomNode)
            si_->freeState(state);
    }

    bool solved = false;
    bool approximate = false;
    if (solution == nullptr)
    {
        solution = approxsol;
        approximate = true;
    }

    if (solution != nullptr)
    {
        lastGoalMotion_ = solution;

        // Construct the solution path
        std::vector<Motion *> mpath;
        while (solution != nullptr)
        {
            mpath.push_back(solution);
            solution = solution->parent;
        }

        // Set the solution path
        auto path(std::make_shared<PathGeometric>(si_));
        for (int i = mpath.size() - 1; i >= 0; --i)
            path->append(mpath[i]->state);
        pdef_->addSolutionPath(path, approximate, approxdif, getName());
        solved = true;
    }

    si_->freeState(xstate);
    if (rmotion->state != nullptr)
        si_->freeState(rmotion->state);
    delete rmotion;

    OMPL_INFORM("%s: Created %u states", getName().c_str(), nn_->size());

    return {solved, approximate};
}



void ompl::geometric::ICanSeeYou::getPlannerData(base::PlannerData &data) const
{
    Planner::getPlannerData(data);

    std::vector<Motion *> motions;
    if (nn_)
        nn_->list(motions);

    if (lastGoalMotion_ != nullptr)
        data.addGoalVertex(base::PlannerDataVertex(lastGoalMotion_->state));

    for (auto &motion : motions)
    {
        if (motion->parent == nullptr)
            data.addStartVertex(base::PlannerDataVertex(motion->state));
        else
            data.addEdge(base::PlannerDataVertex(motion->parent->state), base::PlannerDataVertex(motion->state));
    }
}
